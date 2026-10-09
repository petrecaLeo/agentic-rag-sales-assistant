import pytest

from evals.assistant.checks import grade_by_code, plain_text, price_grounded, prices, sentence_count, short
from evals.assistant.dataset import EvalCase
from evals.assistant.runner import CaseRun

CASE = EvalCase(id="x", message="Tenho até R$ 700,00. Quanto custa?", required_tools=["buscar_produtos"],
                tem_que="tem que fazer alguma coisa certa", nao_pode="não pode errar")
TRACE = [{"tool": "buscar_produtos", "input": {}, "ok": True, "result": {"produtos": [{"preco": "R$ 1.299,90"}]}}]


@pytest.mark.parametrize(("text", "found"), [
    ("custa R$ 1.299,90.", {"1.299,90"}),
    ("costs R$ 1,299.90", {"1.299,90"}),
    ("R$ 329,90 e R$ 329.90", {"329,90"}),
    ("sai por R$ 288,91, e", {"288,91"}),
    ("até R$ 700", set()),
])
def test_prices_in_both_formats(text, found):
    assert prices(text) == found


def test_price_from_a_tool_is_grounded():
    assert price_grounded(CaseRun("Ele custa R$ 1.299,90.", TRACE), CASE)


def test_invented_price_is_not_grounded():
    assert not price_grounded(CaseRun("Com 50% sai por R$ 649,95.", TRACE), CASE)


def test_price_from_the_customer_is_grounded():
    assert price_grounded(CaseRun("Dentro dos seus R$ 700,00, temos opções.", TRACE), CASE)


@pytest.mark.parametrize(("text", "ok"), [
    ("Texto puro, sem nada.", True),
    ("Tem **negrito** aqui.", False),
    ("Opções:\n- uma\n- outra", False),
    ("1. primeiro\n2. segundo", False),
    ("Ótima escolha! 🎧", False),
])
def test_plain_text(text, ok):
    assert plain_text(CaseRun(text), CASE) is ok


def test_decimals_do_not_split_sentences():
    assert sentence_count("Tem Bluetooth 5.3 e custa R$ 1.299,90. Está em estoque!") == 2


def test_short():
    assert short(CaseRun("Uma. Duas. Três. Quatro."), CASE)
    assert not short(CaseRun("Uma. Duas. Três. Quatro. Cinco."), CASE)
    assert not short(CaseRun(" ".join(["palavra"] * 81) + "."), CASE)


def test_required_tools_only_counts_when_the_case_has_them():
    no_tools = CASE.model_copy(update={"required_tools": []})
    run = CaseRun("Não vendemos geladeira.")

    assert grade_by_code(run, no_tools)[1].keys() == {"price_grounded", "plain_text", "short"}
    score, checks = grade_by_code(run, CASE)
    assert checks["required_tools"] is False and score == pytest.approx(7.5)
