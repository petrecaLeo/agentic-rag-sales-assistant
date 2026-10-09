from collections.abc import Callable
from dataclasses import dataclass
from functools import cache

from backend.catalog.models import Category, Product
from backend.catalog.store import default_catalog
from backend.config import CACHE_DIR, PRODUCT_MIN_SIMILARITY, SEARCH_METHOD
from backend.rag.bm25 import BM25Index
from backend.rag.documents import PolicyChunk, load_policy_chunks, product_text
from backend.rag.embeddings import default_embedder
from backend.rag.hybrid import HybridIndex, Index
from backend.rag.keywords import KeywordIndex
from backend.rag.vector_index import VectorIndex

IndexFactory = Callable[[list[str]], Index]


@dataclass(frozen=True)
class SearchMethod:
    products: IndexFactory
    policy: IndexFactory


def vectors(min_score: float | None = None) -> IndexFactory:
    return lambda texts: VectorIndex(texts, default_embedder(), CACHE_DIR, min_score)


def hybrid(*factories: IndexFactory) -> IndexFactory:
    return lambda texts: HybridIndex([factory(texts) for factory in factories])


# Só os produtos têm nota mínima: na política, até acertos certos têm semelhança baixa (parágrafos longos).
METHODS: dict[str, SearchMethod] = {
    "palavras": SearchMethod(KeywordIndex, KeywordIndex),
    "bm25": SearchMethod(BM25Index, BM25Index),
    "embeddings": SearchMethod(vectors(PRODUCT_MIN_SIMILARITY), vectors()),
    "hibrido": SearchMethod(hybrid(BM25Index, vectors(PRODUCT_MIN_SIMILARITY)), hybrid(BM25Index, vectors())),
}


class ProductSearch:
    def __init__(self, products: list[Product], index_factory: IndexFactory) -> None:
        self.products = products
        self.index = index_factory([product_text(p) for p in products])

    def search(
        self, query: str, limit: int, categoria: Category | None = None, max_cents: int | None = None
    ) -> list[Product]:
        ranked = (self.products[i] for i, _ in self.index.rank(query))
        matching = (
            p for p in ranked
            if (categoria is None or p.categoria == categoria) and (max_cents is None or p.preco <= max_cents)
        )
        return [product for _, product in zip(range(limit), matching)]


class PolicySearch:
    def __init__(self, chunks: list[PolicyChunk], index_factory: IndexFactory) -> None:
        self.chunks = chunks
        self.index = index_factory([chunk.texto for chunk in chunks])

    def search(self, query: str, limit: int) -> list[PolicyChunk]:
        return [self.chunks[i] for i, _ in self.index.rank(query)[:limit]]


@cache
def default_product_search() -> ProductSearch:
    return ProductSearch(default_catalog().products, METHODS[SEARCH_METHOD].products)


@cache
def default_policy_search() -> PolicySearch:
    return PolicySearch(load_policy_chunks(), METHODS[SEARCH_METHOD].policy)
