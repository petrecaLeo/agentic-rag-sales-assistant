import json

from backend.assistant.policy_path import policy_text
from backend.assistant.profiles import PROFILES
from backend.assistant.reply import reply
from backend.config import HAIKU, SONNET
from backend.prompts.router import ROUTER_PROMPT
from backend.routing.router import route
from backend.sessions import Session
from evals.assistant.checks import price_grounded, required_tools
from evals.assistant.dataset import EvalCase
from evals.assistant.runner import CaseRun
from tests.conftest import Reply, text, tool_use


def chosen(name: str) -> Reply:
    return Reply([text(json.dumps({"rota": name}))])


def cited(answer: str, *quotes: str) -> dict:
    citations = [{"type": "char_location", "cited_text": quote, "document_index": 0, "document_title": "Política",
                  "start_char_index": 0, "end_char_index": len(quote)} for quote in quotes]
    return {"type": "text", "text": answer, "citations": citations}


def new_session(messages: list | None = None) -> Session:
    return Session(id="teste", last_seen=0, messages=messages or [])


def test_router_asks_haiku_for_structured_output_with_the_recent_conversation(fake_api):
    fake_api.queue(chosen("politica"))
    history = [{"role": "user", "content": "Quanto custa o frete?"},
               {"role": "assistant", "content": [{"type": "text", "text": "É grátis acima de R$ 299,00."}]}]

    assert route("E se eu pagar no boleto?", history) == "politica"

    body = fake_api.requests[0]
    assert body["model"] == HAIKU and body["thinking"] == {"type": "disabled"}
    assert body["system"] == ROUTER_PROMPT
    assert body["output_config"]["format"]["type"] == "json_schema"
    content = body["messages"][0]["content"]
    assert "assistente: É grátis acima de R$ 299,00." in content and "E se eu pagar no boleto?" in content


def test_router_falls_back_to_the_agent_on_api_error_or_bad_output(fake_api):
    fake_api.queue(Reply(status=500), Reply([text("não sei")]))

    assert route("Qual o prazo de troca?", []) == "produto"
    assert route("Qual o prazo de troca?", []) == "produto"


def test_policy_route_answers_with_the_whole_policy_and_citations(fake_api):
    fake_api.queue(chosen("politica"), Reply([cited("Você tem 7 dias para desistir.", "Arrependimento: se não gostar  do produto")]))
    session = new_session()

    events = list(reply(session, "Posso devolver?", "pt", PROFILES["rota"]))

    assert [e["type"] for e in events] == ["route", "text", "citations"]
    assert events[1]["text"] == "Você tem 7 dias para desistir."
    assert events[2]["items"] == ["Arrependimento: se não gostar do produto"]
    body = fake_api.requests[1]
    document = body["messages"][0]["content"][0]
    assert body["model"] == HAIKU and "stream" not in body
    assert body["thinking"] == {"type": "disabled"} and body["output_config"] == {"effort": "low"}
    assert document["citations"] == {"enabled": True} and document["cache_control"] == {"type": "ephemeral"}
    assert document["source"]["data"] == policy_text()
    assert session.messages == [{"role": "user", "content": "Posso devolver?"},
                                {"role": "assistant", "content": "Você tem 7 dias para desistir."}]


def test_product_route_goes_to_the_agent(fake_api):
    fake_api.queue(chosen("produto"), Reply([text("Temos o Vetor G15.")]))

    events = list(reply(new_session(), "Tem notebook gamer?", "pt", PROFILES["rota"]))

    assert events[0] == {"type": "route", "name": "produto"}
    assert fake_api.requests[1]["model"] == SONNET and fake_api.requests[1]["stream"] is True


def test_profiles_without_router_skip_it(fake_api):
    fake_api.queue(Reply([tool_use("t1", "buscar_politica", {"pergunta": "troca"})], stop_reason="tool_use"),
                   Reply([text("Você tem 7 dias.")]))

    events = list(reply(new_session(), "Posso trocar?", "pt", PROFILES["cache"]))

    assert "route" not in [e["type"] for e in events]
    assert fake_api.requests[0]["model"] == SONNET


CASE = EvalCase(id="politica", message="Até quanto o frete é pago?", required_tools=["buscar_politica"],
                tem_que="dizer o valor mínimo do frete grátis", nao_pode="inventar outro valor")


def test_policy_route_counts_as_reading_the_policy_and_grounds_its_prices():
    run = CaseRun(answer="O frete é grátis acima de R$ 299,00.", route="politica")

    assert required_tools(run, CASE) and price_grounded(run, CASE)
    assert not price_grounded(CaseRun(answer="O frete é grátis acima de R$ 299,00."), CASE)


def test_routing_eval_separates_the_two_kinds_of_error():
    from evals.routing.run import load_dataset, summarize

    results = [
        {"expected": "politica", "got": "politica", "seconds": 0.2},
        {"expected": "politica", "got": "produto", "seconds": 0.4},
        {"expected": "produto", "got": "politica", "seconds": 0.3},
        {"expected": "produto", "got": "produto", "seconds": 0.3},
    ]

    assert summarize(results) == {"accuracy": 0.5, "policy_to_agent": 1, "product_to_policy": 1, "seconds": 0.3}
    cases = load_dataset()
    assert len(cases) == 53 and {c["rota"] for c in cases} == {"politica", "produto"}


def test_the_judge_sees_the_whole_policy_on_the_policy_route():
    from evals.assistant.judge_prompt import format_trace

    trace = format_trace(CaseRun(answer="Você tem 7 dias.", route="politica", citations=["Arrependimento: ..."]))

    assert policy_text() in trace
