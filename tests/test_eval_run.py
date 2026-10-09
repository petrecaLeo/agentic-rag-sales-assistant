import json

from evals.assistant.dataset import EvalCase
from evals.assistant.judge import grade_by_model
from evals.assistant.run_eval import evaluate
from evals.assistant.runner import CaseRun, run_case
from tests.conftest import Reply, text, tool_use

CASE = EvalCase(id="teste", message="Quanto custa o Vetor G15 com 32 GB?", required_tools=["buscar_produtos"],
                tem_que="dizer o preço certo do produto", nao_pode="inventar preço")


def verdict(score: int = 9) -> Reply:
    return Reply([text(json.dumps({"reasoning": "Tudo veio do rastro.", "score": score}))])


def test_run_keeps_only_the_text_after_the_last_tool_and_the_trace(fake_api):
    fake_api.queue(
        Reply([text("Vou buscar."), tool_use("t1", "buscar_produtos", {"consulta": "Vetor G15 32 GB"})], stop_reason="tool_use"),
        Reply([text("O Vetor G15 custa R$ 7.299,90.")]),
    )

    run = run_case(CASE, "v1")

    assert run.answer == "O Vetor G15 custa R$ 7.299,90."
    assert run.trace[0]["tool"] == "buscar_produtos" and run.trace[0]["ok"] is True
    assert run.trace[0]["result"]["produtos"]
    assert run.error is None


def test_run_records_errors(fake_api):
    fake_api.queue(Reply([], stop_reason="refusal"))

    assert run_case(CASE, "v1").error == "refused"


def test_judge_uses_haiku_with_structured_output_and_temperature_zero(fake_api):
    fake_api.queue(verdict(8))

    result = grade_by_model(CASE, CaseRun("O Vetor G15 custa R$ 7.299,90."))

    body = fake_api.requests[0]
    assert result.score == 8
    assert body["model"] == "claude-haiku-4-5" and body["temperature"] == 0
    assert body["output_config"]["format"]["type"] == "json_schema"
    assert "<rastro_das_ferramentas>" in body["messages"][0]["content"]


def test_judge_retries_an_invalid_score(fake_api):
    fake_api.queue(verdict(11), verdict(7))

    assert grade_by_model(CASE, CaseRun("Resposta qualquer.")).score == 7


def test_evaluate_combines_code_and_judge(fake_api):
    fake_api.queue(
        Reply([tool_use("t1", "buscar_produtos", {"consulta": "Vetor G15 32 GB"})], stop_reason="tool_use"),
        Reply([text("Com desconto especial, sai por R$ 1,00.")]),
        verdict(3),
    )

    result = evaluate(CASE, "v1")

    assert result["checks"]["price_grounded"] is False
    assert result["judge_score"] == 3
    assert result["score"] == (result["code_score"] + 3) / 2
