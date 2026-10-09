from dataclasses import dataclass
from pathlib import Path

from backend.catalog.models import CATEGORY_NAMES, Product
from backend.config import POLICY_FILE


@dataclass(frozen=True)
class PolicyChunk:
    tema: str
    texto: str


# Nome e descrição primeiro: o modelo de embeddings só lê o começo do texto.
def product_text(product: Product) -> str:
    attributes = ". ".join(product.atributos.values())
    return f"{product.nome}. {product.descricao} {CATEGORY_NAMES[product.categoria]}. {product.marca}. {attributes}."


def load_policy_chunks(path: Path = POLICY_FILE) -> list[PolicyChunk]:
    paragraphs = [p.strip() for p in path.read_text(encoding="utf-8").split("\n\n") if p.strip()]
    return [PolicyChunk(tema=p.split(":", 1)[0], texto=p) for p in paragraphs]
