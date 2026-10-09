import pytest

from backend.catalog.money import format_brl


@pytest.mark.parametrize(
    ("cents", "text"),
    [(0, "R$ 0,00"), (5, "R$ 0,05"), (4990, "R$ 49,90"), (129990, "R$ 1.299,90"), (1234567, "R$ 12.345,67")],
)
def test_format_brl(cents, text):
    assert format_brl(cents) == text
