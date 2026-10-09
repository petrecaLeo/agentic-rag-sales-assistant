import json

from backend.assistant import loop
from backend.config import ASSISTANT_MAX_ROUNDS
from tests.conftest import Reply, send, text, thinking, tool_use


def kinds(events: list[dict]) -> list[str]:
    return [e["type"] for e in events if e["type"] != "text"]


def test_two_rounds_of_tools_then_an_answer(client, fake_api):
    fake_api.queue(
        Reply([text("Vou procurar."), tool_use("t1", "buscar_produtos", {"consulta": "fone corrida"})], stop_reason="tool_use"),
        Reply([tool_use("t2", "consultar_estoque", {"id": 93})], stop_reason="tool_use"),
        Reply([text("O Fone Pulse Run está disponível.")]),
    )

    status, events = send(client, "tem fone pra corrida?")

    assert status == 200
    assert kinds(events) == ["session", "tool_call", "tool_result", "tool_call", "tool_result", "done"]
    assert events[1] == {"type": "text", "text": "Vou p"}
    assert [e["input"] for e in events if e["type"] == "tool_call"] == [{"consulta": "fone corrida"}, {"id": 93}]
    assert len(fake_api.requests) == 3
    first_result = fake_api.requests[1]["messages"][-1]["content"][0]
    assert first_result["tool_use_id"] == "t1" and "is_error" not in first_result
    assert "R$" in first_result["content"]


def test_parallel_calls_are_answered_in_one_message(client, fake_api):
    fake_api.queue(
        Reply([tool_use("a", "consultar_estoque", {"id": 1}), tool_use("b", "consultar_estoque", {"id": 2})],
              stop_reason="tool_use"),
        Reply([text("Os dois têm estoque.")]),
    )

    send(client, "tem o 1 e o 2?")

    answer = fake_api.requests[1]["messages"][-1]
    assert answer["role"] == "user"
    assert [block["tool_use_id"] for block in answer["content"]] == ["a", "b"]


def test_bad_tool_input_goes_back_as_an_error_and_the_loop_goes_on(client, fake_api):
    fake_api.queue(
        Reply([tool_use("t1", "consultar_estoque", {"id": "abc"})], stop_reason="tool_use"),
        Reply([text("Não consegui consultar esse produto.")]),
    )

    _, events = send(client, "estoque do abc")

    assert [e["ok"] for e in events if e["type"] == "tool_result"] == [False]
    assert fake_api.requests[1]["messages"][-1]["content"][0]["is_error"] is True
    assert events[-1] == {"type": "done"}


def test_loop_stops_after_the_round_limit(client, fake_api, session_store):
    fake_api.queue(*[
        Reply([tool_use(f"t{i}", "consultar_estoque", {"id": 1})], stop_reason="tool_use")
        for i in range(ASSISTANT_MAX_ROUNDS)
    ])

    _, events = send(client, "pergunta sem fim")

    assert events[-1] == {"type": "error", "code": "too_many_steps"}
    assert len(fake_api.requests) == ASSISTANT_MAX_ROUNDS
    session = session_store.open(events[0]["id"])
    assert (session.messages, session.turns) == ([], 0)


def test_a_cut_tool_call_never_runs(client, fake_api, session_store):
    fake_api.queue(Reply([tool_use("t1", "consultar_estoque", {"id": 1})], stop_reason="max_tokens"))

    _, events = send(client, "tem estoque?")

    assert events[-1] == {"type": "error", "code": "incomplete_reply"}
    assert "tool_call" not in kinds(events)
    assert session_store.open(events[0]["id"]).messages == []


def test_refusal_after_a_tool_discards_the_whole_turn(client, fake_api, session_store):
    fake_api.queue(
        Reply([tool_use("t1", "consultar_estoque", {"id": 1})], stop_reason="tool_use"),
        Reply([], stop_reason="refusal"),
    )

    _, events = send(client, "algo recusado")

    assert events[-1] == {"type": "error", "code": "refused"}
    assert session_store.open(events[0]["id"]).messages == []


def test_a_bug_mid_stream_ends_with_an_error_event(client, fake_api, monkeypatch):
    def broken_tool(name, raw_input):
        raise RuntimeError("bug numa tool")

    fake_api.queue(Reply([tool_use("t1", "consultar_estoque", {"id": 1})], stop_reason="tool_use"))
    monkeypatch.setattr(loop, "run_tool", broken_tool)

    _, events = send(client, "tem o produto 1?")

    assert events[-1] == {"type": "error", "code": "stream_interrupted"}
    assert "bug numa tool" not in json.dumps(events)


def test_history_keeps_tool_and_thinking_blocks_unchanged(client, fake_api):
    fake_api.queue(
        Reply([thinking("Vou checar o estoque."), tool_use("t1", "consultar_estoque", {"id": 1})], stop_reason="tool_use"),
        Reply([text("Tem, sim.")]),
        Reply([text("De nada!")]),
    )

    _, first = send(client, "tem o produto 1?")
    send(client, "valeu", session_id=first[0]["id"])

    first_turn = fake_api.requests[1]["messages"]
    next_turn = fake_api.requests[2]["messages"]
    assert next_turn[: len(first_turn)] == first_turn
    assert [m["role"] for m in next_turn] == ["user", "assistant", "user", "assistant", "user"]
    assert next_turn[1]["content"][0] == {
        "type": "thinking", "thinking": "Vou checar o estoque.", "signature": "assinatura-falsa",
    }
    stock = json.loads(next_turn[2]["content"][0]["content"])
    assert stock["id"] == 1
