from functools import cache
from typing import Protocol

import numpy as np

from backend.config import CACHE_DIR, EMBEDDING_MODEL


class Embedder(Protocol):
    name: str

    def embed(self, texts: list[str]) -> np.ndarray: ...


def unit_rows(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.where(norms == 0, 1, norms)


class FastEmbedder:
    def __init__(self, model_name: str = EMBEDDING_MODEL) -> None:
        # Importado só aqui: carregar o onnxruntime e o modelo leva segundos, e os testes nunca precisam.
        from fastembed import TextEmbedding

        self.name = model_name
        self.model = TextEmbedding(model_name=model_name, cache_dir=str(CACHE_DIR / "models"))

    def embed(self, texts: list[str]) -> np.ndarray:
        return unit_rows(np.array(list(self.model.embed(texts)), dtype=np.float32))


@cache
def default_embedder() -> Embedder:
    return FastEmbedder()
