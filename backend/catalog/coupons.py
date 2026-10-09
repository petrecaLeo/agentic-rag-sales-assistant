import json
from datetime import date
from functools import cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from backend.catalog.models import CATEGORY_NAMES, Coupon, PaymentMethod, Product
from backend.catalog.money import format_brl
from backend.config import COUPONS_FILE

Reason = Literal["ok", "cupom_inexistente", "cupom_vencido", "categoria_nao_aceita", "valor_minimo", "exige_pix"]


class CouponResult(BaseModel):
    valido: bool
    motivo: Reason
    detalhe: str
    preco_original: int
    desconto: int
    preco_final: int


def load_coupons(path: Path = COUPONS_FILE) -> dict[str, Coupon]:
    coupons = [Coupon.model_validate(item) for item in json.loads(path.read_text(encoding="utf-8"))]
    return {coupon.codigo: coupon for coupon in coupons}


@cache
def default_coupons() -> dict[str, Coupon]:
    return load_coupons()


def validate_coupon(
    code: str,
    product: Product,
    payment: PaymentMethod | None,
    coupons: dict[str, Coupon],
    today: date,
) -> CouponResult:
    price = product.preco

    def rejected(reason: Reason, detail: str) -> CouponResult:
        return CouponResult(
            valido=False, motivo=reason, detalhe=detail, preco_original=price, desconto=0, preco_final=price
        )

    coupon = coupons.get(code.strip().upper())
    if coupon is None:
        return rejected("cupom_inexistente", f"O cupom {code.strip()} não existe.")
    if coupon.validade and today > coupon.validade:
        return rejected("cupom_vencido", f"O cupom {coupon.codigo} venceu em {coupon.validade:%d/%m/%Y}.")
    if coupon.categorias and product.categoria not in coupon.categorias:
        names = " e ".join(CATEGORY_NAMES[c] for c in coupon.categorias)
        return rejected("categoria_nao_aceita", f"O cupom {coupon.codigo} vale só para {names}.")
    if price < coupon.minimo:
        return rejected(
            "valor_minimo", f"O cupom {coupon.codigo} vale só para produtos a partir de {format_brl(coupon.minimo)}."
        )
    if coupon.pagamento == "pix" and payment != "pix":
        return rejected("exige_pix", f"O cupom {coupon.codigo} vale só para pagamento no Pix.")

    if coupon.tipo == "percentual":
        discount = (price * coupon.valor + 50) // 100
    else:
        discount = min(coupon.valor, price)
    return CouponResult(
        valido=True,
        motivo="ok",
        detalhe=f"O cupom {coupon.codigo} vale para este produto.",
        preco_original=price,
        desconto=discount,
        preco_final=price - discount,
    )
