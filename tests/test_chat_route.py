import pytest

from backend import llm
from backend.config import ASSISTANT_MODEL
from tests.conftest import Reply, send, text


def reply_text(events: list[dict]) -> str:
    return "".join(e["text"] for e in events if e["type"] == "text")


def test_streams_session_then_text_then_done(client, fake_api):
    fake_api.queue(Reply([text("Oi! Sou o assistente da Circuito.")]))

    status, events = send(client, "oi")

    assert status == 200
    assert events[0]["type"] == "session" and len(events[0]["id"]) == 32
    assert reply_text(events) == "Oi! Sou o assistente da Circuito."
    assert len([e for e in events if e["type"] == "text"]) > 1
    assert events[-1] == {"type": "done"}


def test_request_uses_sonnet_settings(client, fake_api):
    fake_api.queue(Reply())

    send(client, "oi", language="en")

    body = fake_api.requests[0]
    assert body["model"] == ASSISTANT_MODEL
    assert body["thinking"] == {"type": "between_tools"}
    assert body["output_config"] == {"effort": "low"}
    assert "temperature" not in body
    assert "inglês" in body["system"]


def test_history_lives_on_the_server(client, fake_api):
    fake_api.queue(Reply([text("Prazer, Ana!")]), Reply([text("Seu nome é Ana.")]))

    _, first = send(client, "meu nome é Ana")
    session_id = first[0]["id"]
    _, second = send(client, "qual é meu nome?", session_id=session_id)

    assert second[0]["id"] == session_id
    sent = fake_api.requests[1]["messages"]
    assert [m["role"] for m in sent] == ["user", "assistant", "user"]
    assert sent[0]["content"] == "meu nome é Ana"
    assert sent[1]["content"][0]["text"] == "Prazer, Ana!"


def test_unknown_session_starts_a_new_one(client, fake_api):
    fake_api.queue(Reply())

    _, events = send(client, "oi", session_id="0" * 32)

    assert events[0]["id"] != "0" * 32
    assert len(fake_api.requests[0]["messages"]) == 1


def test_failed_turn_does_not_enter_the_history(client, fake_api, session_store):
    fake_api.queue(Reply([text("Primeira resposta.")]), Reply(fail_after_events=4), Reply([text("Agora foi.")]))

    _, first = send(client, "primeira")
    session_id = first[0]["id"]
    _, broken = send(client, "segunda", session_id=session_id)
    send(client, "terceira", session_id=session_id)

    assert broken[-1] == {"type": "error", "code": "stream_interrupted"}
    sent = fake_api.requests[2]["messages"]
    assert [m["content"] for m in sent if m["role"] == "user"] == ["primeira", "terceira"]


def test_refusal_becomes_an_error_and_is_not_saved(client, fake_api, session_store):
    fake_api.queue(Reply([], stop_reason="refusal"))

    _, events = send(client, "algo recusado")

    assert events[-1] == {"type": "error", "code": "refused"}
    assert session_store.open(events[0]["id"]).messages == []


@pytest.mark.parametrize(("status", "code", "http_status"), [(401, "invalid_api_key", 500), (529, "api_unavailable", 502)])
def test_api_errors_before_the_stream_get_a_real_status(client, fake_api, status, code, http_status):
    fake_api.queue(Reply(status=status))

    assert send(client, "oi") == (http_status, [{"code": code}])


def test_missing_key_is_a_clear_error(client, monkeypatch):
    monkeypatch.setattr(llm, "_client", None)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    assert send(client, "oi") == (500, [{"code": "missing_api_key"}])


def test_conversation_has_a_turn_limit(client, fake_api, session_store):
    session_store.max_turns = 2
    fake_api.queue(Reply(), Reply())

    _, first = send(client, "um")
    session_id = first[0]["id"]
    send(client, "dois", session_id=session_id)

    assert send(client, "três", session_id=session_id) == (409, [{"code": "conversation_too_long"}])


def test_a_reply_that_raced_another_one_is_discarded(client, fake_api, session_store, monkeypatch):
    fake_api.queue(Reply([text("Resposta um.")]), Reply([text("Resposta dois.")]))
    _, first = send(client, "um")
    session = session_store.open(first[0]["id"])
    answer = fake_api.handler

    def other_reply_is_saved_meanwhile(request):
        other = [{"role": "user", "content": "outra"}, {"role": "assistant", "content": "Outra resposta."}]
        session.commit(other, started_at_turn=session.turns)
        return answer(request)

    monkeypatch.setattr(fake_api, "handler", other_reply_is_saved_meanwhile)
    monkeypatch.setattr(llm, "_client", fake_api.client)

    _, events = send(client, "dois", session_id=session.id)

    assert events[-1] == {"type": "error", "code": "busy"}
    assert [m["content"] for m in session.messages if m["role"] == "user"] == ["um", "outra"]
    assert session.turns == 2


@pytest.mark.parametrize(
    "body",
    [
        {"message": ""},
        {"message": "   "},
        {"message": "x" * 1001},
        {"message": "oi", "session_id": "nao-e-um-id"},
        {"message": "oi", "language": "es"},
        {"message": "oi", "messages": []},
    ],
)
def test_invalid_requests_never_reach_the_api(client, fake_api, body):
    response = client.post("/api/chat", json=body)

    assert (response.status_code, response.json()) == (422, {"code": "invalid_request"})
    assert fake_api.requests == []


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}
