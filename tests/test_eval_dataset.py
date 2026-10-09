from datetime import date

from backend.catalog.coupons import default_coupons, validate_coupon
from backend.catalog.money import format_brl
from backend.catalog.store import default_catalog
from evals.assistant.checks import prices
from evals.assistant.dataset import load_dataset

CASES = load_dataset()


def test_dataset_loads():
    assert len(CASES) == 15
    assert {c.language for c in CASES} == {"pt", "en"}


def test_every_price_in_the_expected_answers_is_real():
    catalog = default_catalog().products
    real = {format_brl(p.preco).removeprefix("R$ ") for p in catalog}
    for code in default_coupons():
        for product in catalog:
            for payment in (None, "pix"):
                result = validate_coupon(code, product, payment, default_coupons(), date(2026, 10, 8))
                real.add(format_brl(result.preco_final).removeprefix("R$ "))
    for case in CASES:
        assert prices(case.tem_que) <= real, case.id
