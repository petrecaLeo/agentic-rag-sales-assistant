from itertools import chain

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.assistant.loop import stream_reply
from backend.schemas import ChatRequest
from backend.sessions import sessions
from backend.stream_events import as_ndjson, event

router = APIRouter()


@router.post("/chat")
def chat(request: ChatRequest) -> StreamingResponse:
    session = sessions.open(request.session_id)
    replies = stream_reply(session, request.message, request.language)
    # Puxado antes de responder: um erro de chave ou de conexão ainda vira um status HTTP de verdade.
    first = next(replies, None)
    events = chain([event("session", id=session.id)], [first] if first else [], replies)
    return StreamingResponse(as_ndjson(events), media_type="application/x-ndjson")
