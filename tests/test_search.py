from backend.catalog.store import default_catalog
from backend.rag.documents import load_policy_chunks, product_text
from backend.rag.search import default_policy_search, default_product_search

CATALOG = default_catalog()
PRODUCTS = default_product_search()


def test_product_text_starts_with_name_and_description():
    product = CATALOG.get(93)

    assert product_text(product).startswith(f"{product.nome}. {product.descricao}")


def test_name_queries_hit_the_right_product():
    assert PRODUCTS.search("Vetor G15 32 GB", 1)[0].id == 58
    assert PRODUCTS.search("capa nimbus 8", 1)[0].id == 179


def test_filters_apply_after_ranking():
    found = PRODUCTS.search("notebook para trabalho", 5, categoria="notebooks", max_cents=400000)

    assert found
    assert all(p.categoria == "notebooks" and p.preco <= 400000 for p in found)


def test_limit():
    assert len(PRODUCTS.search("fone", 3)) == 3


def test_policy_is_split_by_topic():
    chunks = load_policy_chunks()

    assert [c.tema for c in chunks][:3] == ["Sobre esta política", "Frete", "Prazo de entrega"]
    assert all(c.texto.startswith(f"{c.tema}:") for c in chunks)


def test_policy_search():
    assert default_policy_search().search("o frete é grátis?", 1)[0].tema == "Frete"
