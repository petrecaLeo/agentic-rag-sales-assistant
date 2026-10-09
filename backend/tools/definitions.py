from pydantic import BaseModel

from backend.tools.inputs import PolicyInput, ProductIdInput, SearchProductsInput, ValidateCouponInput

TOOL_INPUTS: dict[str, type[BaseModel]] = {
    "buscar_produtos": SearchProductsInput,
    "consultar_produto": ProductIdInput,
    "consultar_estoque": ProductIdInput,
    "validar_cupom": ValidateCouponInput,
    "buscar_politica": PolicyInput,
}

DESCRIPTIONS = {
    "buscar_produtos": (
        "Busca produtos no catálogo da Circuito pelo nome ou pela necessidade do cliente. "
        "Devolve até 5 produtos com id, nome, categoria, preço e descrição, sem estoque. "
        "Se nada servir, tente de novo com outras palavras antes de dizer que a loja não tem. "
        "O catálogo está em português: escreva a consulta em português, mesmo que o cliente use outro idioma."
    ),
    "consultar_produto": (
        "Devolve os detalhes de um produto pelo id: marca, preço, atributos técnicos e descrição. Não traz estoque."
    ),
    "consultar_estoque": (
        "Diz quantas unidades de um produto há em estoque. Use antes de afirmar que um produto está disponível ou esgotado."
    ),
    "validar_cupom": (
        "Confere se um cupom vale para um produto e devolve o preço original, o desconto e o preço final já calculados. "
        "Se não valer, explica o motivo. Use sempre que o cliente citar um cupom; nunca calcule desconto por conta própria."
    ),
    "buscar_politica": (
        "Busca na política da loja os trechos sobre frete, prazo de entrega, pagamento, cupons, trocas, devoluções, "
        "garantia, reembolso e atendimento. Devolve até 3 trechos. Use para qualquer dúvida sobre essas regras. "
        "A política está em português: escreva a pergunta em português, mesmo que o cliente use outro idioma."
    ),
}


def without_titles(node):
    if isinstance(node, dict):
        return {key: without_titles(value) for key, value in node.items() if key != "title"}
    if isinstance(node, list):
        return [without_titles(value) for value in node]
    return node


TOOLS = [
    {
        "name": name,
        "description": DESCRIPTIONS[name],
        # O schema sai do mesmo pydantic que valida a entrada: o que o Claude vê e o que o código aceita não divergem.
        "input_schema": without_titles(model.model_json_schema()),
        "eager_input_streaming": True,
    }
    for name, model in TOOL_INPUTS.items()
]
