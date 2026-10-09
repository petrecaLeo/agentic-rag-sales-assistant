from backend.catalog.coupons import default_coupons
from backend.catalog.store import default_catalog
from backend.config import DESCRIPTION_MAX_WORDS, POLICY_FILE
from data.generator import draw_products
from data.generator.describe import WORD_TOLERANCE

CATALOG = default_catalog()


def test_catalog_file_matches_the_seeded_draw():
    drawn = draw_products()

    assert len(CATALOG) == len(drawn) == 220
    for saved, expected in zip(CATALOG.products, drawn):
        assert saved.model_dump(exclude={"descricao"}) == expected.model_dump(exclude={"descricao"})


def test_every_product_has_a_short_description_without_prices():
    for product in CATALOG.products:
        words = len(product.descricao.split())
        assert 15 <= words <= DESCRIPTION_MAX_WORDS + WORD_TOLERANCE, product.id
        assert "R$" not in product.descricao, product.id


def test_lookup_by_id():
    assert CATALOG.get(1).nome == "Aurora Neo 128 GB"
    assert CATALOG.get(9999) is None


def test_coupons_file():
    assert set(default_coupons()) == {"BEMVINDO10", "FONE15", "NOTE200", "VERAO25", "PIX5"}


def test_policy_is_one_topic_per_paragraph():
    paragraphs = [p for p in POLICY_FILE.read_text(encoding="utf-8").split("\n\n") if p.strip()]

    assert len(paragraphs) >= 12
    assert all(0 < p.find(":") < 45 for p in paragraphs)
