from collections import Counter

from data.generator import draw_products

PRODUCTS = draw_products()


def test_same_seed_same_catalog():
    assert [p.model_dump() for p in draw_products()] == [p.model_dump() for p in PRODUCTS]


def test_counts_ids_and_names():
    assert Counter(p.categoria for p in PRODUCTS) == {"celulares": 50, "notebooks": 40, "fones": 60, "acessorios": 70}
    assert [p.id for p in PRODUCTS] == list(range(1, len(PRODUCTS) + 1))
    assert len({p.nome for p in PRODUCTS}) == len(PRODUCTS)


def test_prices_are_cents_ending_in_90():
    assert all(p.preco % 100 == 90 and p.preco > 0 for p in PRODUCTS)


def test_some_products_are_out_of_stock_but_not_many():
    out = sum(p.estoque == 0 for p in PRODUCTS)

    assert 0 < out <= len(PRODUCTS) * 0.2


def test_notebook_coupon_has_cases_on_both_sides_of_the_minimum():
    prices = [p.preco for p in PRODUCTS if p.categoria == "notebooks"]

    assert min(prices) < 300000 < max(prices)


def test_variants_of_the_same_model_share_attributes_except_storage():
    phones = [p for p in PRODUCTS if p.categoria == "celulares"]
    for small, large in zip(phones[::2], phones[1::2]):
        assert {k: v for k, v in small.atributos.items() if k != "armazenamento"} == {
            k: v for k, v in large.atributos.items() if k != "armazenamento"
        }
        assert large.preco > small.preco


def test_every_case_fits_a_phone_in_the_catalog():
    phone_names = {p.nome for p in PRODUCTS if p.categoria == "celulares"}
    cases = [p for p in PRODUCTS if p.atributos.get("tipo") == "capa de celular"]

    assert cases
    for case in cases:
        model = case.atributos["compatível com"].split(" (")[0]
        assert any(name.startswith(model + " ") for name in phone_names)
