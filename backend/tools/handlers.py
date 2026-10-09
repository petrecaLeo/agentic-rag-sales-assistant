import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date

from pydantic import BaseModel, ValidationError

from backend.catalog.coupons import default_coupons, validate_coupon
from backend.catalog.models import Coupon, Product
from backend.catalog.money import format_brl
from backend.catalog.store import Catalog, default_catalog
from backend.config import POLICY_LIMIT, SEARCH_LIMIT
from backend.rag.search import PolicySearch, ProductSearch, default_policy_search, default_product_search
from backend.tools.definitions import TOOL_INPUTS
from backend.tools.inputs import PolicyInput, ProductIdInput, SearchProductsInput, ValidateCouponInput


class ToolError(Exception):
    pass


@dataclass
class ToolContext:
    catalog: Catalog = field(default_factory=default_catalog)
    coupons: dict[str, Coupon] = field(default_factory=default_coupons)
    today: date = field(default_factory=date.today)
    product_search: ProductSearch = field(default_factory=default_product_search)
    policy_search: PolicySearch = field(default_factory=default_policy_search)


@dataclass
class ToolOutcome:
    data: dict
    is_error: bool = False

    def as_block(self, tool_use_id: str) -> dict:
        block = {"type": "tool_result", "tool_use_id": tool_use_id, "content": json.dumps(self.data, ensure_ascii=False)}
        if self.is_error:
            block["is_error"] = True
        return block


def summary(product: Product) -> dict:
    return {"id": product.id, "nome": product.nome, "categoria": product.categoria, "preco": format_brl(product.preco)}


def find(context: ToolContext, product_id: int) -> Product:
    product = context.catalog.get(product_id)
    if product is None:
        raise ToolError(f"Não existe produto com id {product_id}. Use buscar_produtos para achar o id certo.")
    return product


def search_products(args: SearchProductsInput, context: ToolContext) -> dict:
    max_cents = round(args.preco_max * 100) if args.preco_max else None
    found = context.product_search.search(args.consulta, SEARCH_LIMIT, args.categoria, max_cents)
    if not found:
        return {"produtos": [], "dica": "Nada encontrado. Tente outras palavras ou tire os filtros."}
    return {"produtos": [{**summary(p), "descricao": p.descricao} for p in found]}


def product_details(args: ProductIdInput, context: ToolContext) -> dict:
    product = find(context, args.id)
    return {**summary(product), "marca": product.marca, "atributos": product.atributos, "descricao": product.descricao}


def stock(args: ProductIdInput, context: ToolContext) -> dict:
    product = find(context, args.id)
    return {"id": product.id, "nome": product.nome, "estoque": product.estoque, "disponivel": product.estoque > 0}


def coupon(args: ValidateCouponInput, context: ToolContext) -> dict:
    product = find(context, args.produto_id)
    result = validate_coupon(args.codigo, product, args.forma_pagamento, context.coupons, context.today)
    return {
        "cupom": args.codigo.strip().upper(),
        "produto_id": product.id,
        "produto": product.nome,
        "valido": result.valido,
        "motivo": result.motivo,
        "detalhe": result.detalhe,
        "preco_original": format_brl(result.preco_original),
        "desconto": format_brl(result.desconto),
        "preco_final": format_brl(result.preco_final),
    }


def policy(args: PolicyInput, context: ToolContext) -> dict:
    chunks = context.policy_search.search(args.pergunta, POLICY_LIMIT)
    if not chunks:
        return {"trechos": [], "dica": "Nada encontrado na política. Tente outras palavras."}
    return {"trechos": [{"tema": chunk.tema, "texto": chunk.texto} for chunk in chunks]}


HANDLERS: dict[str, Callable[[BaseModel, ToolContext], dict]] = {
    "buscar_produtos": search_products,
    "consultar_produto": product_details,
    "consultar_estoque": stock,
    "validar_cupom": coupon,
    "buscar_politica": policy,
}


def run_tool(name: str, raw_input: object, context: ToolContext | None = None) -> ToolOutcome:
    if name not in HANDLERS:
        return ToolOutcome({"erro": f"A ferramenta {name} não existe."}, is_error=True)
    try:
        args = TOOL_INPUTS[name].model_validate(raw_input)
    except ValidationError as error:
        problems = [f"{'.'.join(map(str, e['loc'])) or 'entrada'}: {e['msg']}" for e in error.errors()]
        return ToolOutcome({"erro": "Entrada inválida.", "problemas": problems}, is_error=True)
    try:
        return ToolOutcome(HANDLERS[name](args, context or ToolContext()))
    except ToolError as error:
        return ToolOutcome({"erro": str(error)}, is_error=True)
