from collections.abc import Iterator
from functools import cache

from anthropic.types import Message

from backend.assistant.history_text import recent_conversation
from backend.config import CONTEXT_MESSAGE_CHARS, CONTEXT_MESSAGES, HAIKU, POLICY_FILE, POLICY_MAX_TOKENS
from backend.llm import get_client, log_cost
from backend.prompts.policy import build_policy_system, policy_question
from backend.sessions import Session
from backend.stream_events import event


@cache
def policy_text() -> str:
    return POLICY_FILE.read_text(encoding="utf-8")


def policy_params(message: str, language: str, conversation: str) -> dict:
    document = {
        "type": "document",
        "source": {"type": "text", "media_type": "text/plain", "data": policy_text()},
        "title": "Política da Circuito",
        "citations": {"enabled": True},
        # A política é igual para todos os clientes: o cache fica no fim dela, antes da pergunta.
        "cache_control": {"type": "ephemeral"},
    }
    return {
        "model": HAIKU,
        "max_tokens": POLICY_MAX_TOKENS,
        "system": build_policy_system(language),
        "messages": [{"role": "user", "content": [document, {"type": "text", "text": policy_question(message, conversation)}]}],
        # Com citations e o effort padrão, o Haiku 5.5 chegou a gastar todo o max_tokens num thinking vazio,
        # mesmo desligado (medido na s4d1). Com effort low ele responde normalmente.
        "thinking": {"type": "disabled"},
        "output_config": {"effort": "low"},
    }


def answer_and_citations(response: Message) -> tuple[str, list[str]]:
    texts = [block for block in response.content if block.type == "text"]
    answer = "".join(block.text for block in texts).strip()
    citations = []
    for block in texts:
        for citation in block.citations or []:
            quoted = " ".join(citation.cited_text.split())
            if quoted not in citations:
                citations.append(quoted)
    return answer, citations


def policy_reply(session: Session, text: str, language: str) -> Iterator[dict]:
    started_at_turn = session.turns
    conversation = recent_conversation(session.messages, CONTEXT_MESSAGES, CONTEXT_MESSAGE_CHARS)
    response = get_client().messages.create(**policy_params(text, language, conversation))
    log_cost("politica", HAIKU, response)
    if response.stop_reason == "refusal":
        yield event("error", code="refused")
        return
    answer, citations = answer_and_citations(response)
    if not answer:
        yield event("error", code="empty_reply")
        return
    yield event("text", text=answer)
    yield event("citations", items=citations)
    if not session.commit([{"role": "user", "content": text}, {"role": "assistant", "content": answer}], started_at_turn):
        yield event("error", code="busy")
