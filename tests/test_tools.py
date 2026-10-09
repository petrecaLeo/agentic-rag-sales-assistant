import json
from datetime import date

import pytest

from backend.catalog.money import format_brl
from backend.catalog.store import default_catalog
from backend.tools.definitions import TOOL_INPUTS, TOOLS
from backend.rag.bm25 import BM25Index
from backend.rag.documents import load_policy_chunks
from backend.rag.search import PolicySearch
from backend.tools.handlers import HANDLERS, ToolContext, run_tool

CONTEXT = ToolContext(today=date(2026, 10, 8))
CATALOG = default_catalog()


def test_every_tool_has_a_handler_a_clean_schema_and_eager_streaming():
    assert [t["name"] for t in TOOLS] == list(TOOL_INPUTS) == list(HANDLERS)
    for tool in TOOLS:
        assert tool["eager_input_streaming"] is True
        assert tool["input_schema"]["additionalProperties"] is False
        assert '"title"' not in json.dumps(tool["input_schema"])


def test_search_finds_by_need_and_hides_stock():
    products = run_tool("buscar_produtos", {"consulta": "fone para corrida"}, CONTEXT).data["produtos"]

    assert products
    assert all(p["preco"].startswith("R$ ") and p["descricao"] and "estoque" not in p for p in products)


def test_search_ignores_accents_and_case():
    first = run_tool("buscar_produtos", {"consulta": "CONDUCAO OSSEA"}, CONTEXT).data["produtos"][0]

    assert CATALOG.get(first["id"]).atributos["tipo"] == "condução óssea sem fio"


def test_search_filters_by_category_and_max_price():
    args = {"consulta": "notebook para trabalho", "categoria": "notebooks", "preco_max": 4000}
    products = run_tool("buscar_produtos", args, CONTEXT).data["produtos"]

    assert products
    for item in products:
        product = CATALOG.get(item["id"])
        assert product.categoria == "notebooks" and product.preco <= 400000


def test_search_without_results_is_not_an_error():
    outcome = run_tool("buscar_produtos", {"consulta": "geladeira frost free"}, CONTEXT)

    assert not outcome.is_error
    assert outcome.data["produtos"] == [] and "dica" in outcome.data


def test_details_and_stock():
    product = CATALOG.get(93)

    details = run_tool("consultar_produto", {"id": 93}, CONTEXT).data
    assert details["preco"] == format_brl(product.preco)
    assert details["atributos"] == product.atributos and "estoque" not in details

    stock = run_tool("consultar_estoque", {"id": 93}, CONTEXT).data
    assert stock == {"id": 93, "nome": product.nome, "estoque": product.estoque, "disponivel": product.estoque > 0}


def test_unknown_product_explains_what_to_do():
    outcome = run_tool("consultar_estoque", {"id": 9999}, CONTEXT)

    assert outcome.is_error and "buscar_produtos" in outcome.data["erro"]


@pytest.mark.parametrize("bad", [{"id": "abc"}, {}, {"id": 1, "extra": True}, {"id": 0}, "não é um objeto"])
def test_invalid_input_becomes_an_error_result(bad):
    outcome = run_tool("consultar_estoque", bad, CONTEXT)

    assert outcome.is_error and outcome.data["erro"] == "Entrada inválida."


@pytest.mark.parametrize("preco_max", [-5, 1_000_001, 1e308, float("inf"), float("nan")])
def test_absurd_max_price_is_an_error_result_not_a_crash(preco_max):
    outcome = run_tool("buscar_produtos", {"consulta": "fone", "preco_max": preco_max}, CONTEXT)

    assert outcome.is_error and outcome.data["erro"] == "Entrada inválida."


def test_unknown_tool():
    assert run_tool("apagar_tudo", {}, CONTEXT).is_error


def test_coupon_money_comes_formatted_and_calculated():
    notebook = CATALOG.get(57)
    data = run_tool("validar_cupom", {"codigo": "note200", "produto_id": 57}, CONTEXT).data

    assert (data["valido"], data["cupom"], data["desconto"], data["produto_id"]) == (True, "NOTE200", "R$ 200,00", 57)
    assert data["preco_final"] == format_brl(notebook.preco - 20000)


def test_rejected_coupon_is_an_answer_not_an_error():
    outcome = run_tool("validar_cupom", {"codigo": "VERAO25", "produto_id": 1}, CONTEXT)

    assert not outcome.is_error
    assert (outcome.data["valido"], outcome.data["motivo"]) == (False, "cupom_vencido")


def test_tool_result_block():
    block = run_tool("consultar_estoque", {"id": 9999}, CONTEXT).as_block("toolu_1")

    assert (block["type"], block["tool_use_id"], block["is_error"]) == ("tool_result", "toolu_1", True)
    assert json.loads(block["content"])["erro"]


def test_policy_tool_returns_topic_and_text():
    passages = run_tool("buscar_politica", {"pergunta": "o frete é grátis?"}, CONTEXT).data["trechos"]

    assert passages[0]["tema"] == "Frete" and passages[0]["texto"].startswith("Frete:")


def test_policy_tool_always_brings_the_closest_passages():
    assert len(run_tool("buscar_politica", {"pergunta": "xyzzy"}, CONTEXT).data["trechos"]) == 3


def test_policy_tool_without_results_gives_a_hint():
    bm25_only = ToolContext(today=date(2026, 10, 8), policy_search=PolicySearch(load_policy_chunks(), BM25Index))
    data = run_tool("buscar_politica", {"pergunta": "xyzzy"}, bm25_only).data

    assert data["trechos"] == [] and "dica" in data
