import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from uuid import uuid4

from anthropic.types import MessageParam

from backend.config import MAX_SESSIONS, MAX_TURNS_PER_SESSION, SESSION_TTL_SECONDS


class ConversationTooLong(Exception):
    pass


@dataclass
class Session:
    id: str
    last_seen: float
    messages: list[MessageParam] = field(default_factory=list)
    turns: int = 0
    # Travado só na hora de salvar. Um lock durante o stream inteiro ficaria preso quando o cliente desconecta:
    # o gerador da resposta só fecha quando o coletor de lixo passa.
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def commit(self, new_messages: list[MessageParam], started_at_turn: int) -> bool:
        # Nunca reescreve: o Sonnet 5.5 confere que o começo da conversa não mudou.
        # Se outra resposta desta sessão foi salva no meio, esta partiu de um histórico velho e é descartada.
        with self._lock:
            if self.turns != started_at_turn:
                return False
            self.messages.extend(new_messages)
            self.turns += 1
            return True


class SessionStore:
    def __init__(
        self,
        ttl: float = SESSION_TTL_SECONDS,
        max_sessions: int = MAX_SESSIONS,
        max_turns: int = MAX_TURNS_PER_SESSION,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.ttl = ttl
        self.max_sessions = max_sessions
        self.max_turns = max_turns
        self.clock = clock
        self._sessions: dict[str, Session] = {}
        # As rotas síncronas do FastAPI rodam em várias threads ao mesmo tempo.
        self._lock = threading.Lock()

    def open(self, session_id: str | None) -> Session:
        with self._lock:
            now = self.clock()
            self._drop_expired(now)
            session = self._sessions.get(session_id) if session_id else None
            if session is None:
                session = self._create(now)
            if session.turns >= self.max_turns:
                raise ConversationTooLong(session.id)
            session.last_seen = now
            return session

    def __len__(self) -> int:
        return len(self._sessions)

    def _create(self, now: float) -> Session:
        if len(self._sessions) >= self.max_sessions:
            oldest = min(self._sessions.values(), key=lambda s: s.last_seen)
            del self._sessions[oldest.id]
        session = Session(id=uuid4().hex, last_seen=now)
        self._sessions[session.id] = session
        return session

    def _drop_expired(self, now: float) -> None:
        for session in [s for s in self._sessions.values() if now - s.last_seen > self.ttl]:
            del self._sessions[session.id]


sessions = SessionStore()
