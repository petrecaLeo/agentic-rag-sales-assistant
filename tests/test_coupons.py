from datetime import date

import pytest

from backend.catalog.coupons import load_coupons, validate_coupon
from backend.catalog.models import Product

TODAY = date(2026, 10, 8)
COUPONS = load_coupons()


def product(categoria="celulares", preco=199990) -> Product:
    return Product(id=1, nome="Produto", categoria=categoria, marca="Marca", preco=preco, estoque=1, atributos={})


def check(code, item, payment=None, today=TODAY):
    return validate_coupon(code, item, payment, COUPONS, today)


def test_percentage_coupon():
    result = check("BEMVINDO10", product(preco=199990))

    assert (result.valido, result.desconto, result.preco_final) == (True, 19999, 179991)


def test_percentage_rounds_half_up_to_the_cent():
    assert check("BEMVINDO10", product(preco=12345)).desconto == 1235


def test_code_is_case_and_space_insensitive():
    assert check("  bemvindo10 ", product()).valido


def test_unknown_coupon():
    result = check("DESCONTO50", product())

    assert (result.valido, result.motivo, result.preco_final) == (False, "cupom_inexistente", 199990)


def test_category_coupon():
    assert check("FONE15", product(categoria="fones", preco=29990)).desconto == 4499
    result = check("FONE15", product(categoria="notebooks"))
    assert (result.valido, result.motivo) == (False, "categoria_nao_aceita")
    assert "fones de ouvido" in result.detalhe


@pytest.mark.parametrize(("price", "valid"), [(299990, False), (300000, True), (459990, True)])
def test_fixed_coupon_with_minimum(price, valid):
    result = check("NOTE200", product(categoria="notebooks", preco=price))

    assert result.valido is valid
    if valid:
        assert (result.desconto, result.preco_final) == (20000, price - 20000)
    else:
        assert result.motivo == "valor_minimo" and "R$ 3.000,00" in result.detalhe


def test_expired_coupon():
    result = check("VERAO25", product())

    assert (result.valido, result.motivo) == (False, "cupom_vencido")
    assert "20/03/2026" in result.detalhe


def test_expiry_day_still_counts():
    assert check("VERAO25", product(), today=date(2026, 3, 20)).valido


@pytest.mark.parametrize(("payment", "valid"), [("pix", True), ("cartao", False), (None, False)])
def test_pix_only_coupon(payment, valid):
    result = check("PIX5", product(), payment)

    assert result.valido is valid
    if not valid:
        assert result.motivo == "exige_pix"


def test_rejected_coupon_keeps_the_original_price():
    result = check("VERAO25", product(preco=50000))

    assert (result.preco_original, result.desconto, result.preco_final) == (50000, 0, 50000)
