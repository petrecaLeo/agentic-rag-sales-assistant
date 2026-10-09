import hashlib
from pathlib import Path

import numpy as np

from backend.rag.embeddings import Embedder


def cache_key(model_name: str, texts: list[str]) -> str:
    digest = hashlib.sha256(model_name.encode())
    for text in texts:
        digest.update(b"\0" + text.encode())
    return digest.hexdigest()[:16]


class VectorIndex:
    def __init__(
        self, texts: list[str], embedder: Embedder, cache_dir: Path | None = None, min_score: float | None = None
    ) -> None:
        self.embedder = embedder
        self.min_score = min_score
        self.vectors = self._load_or_embed(texts, cache_dir)

    def _load_or_embed(self, texts: list[str], cache_dir: Path | None) -> np.ndarray:
        # A chave muda junto com o texto ou o modelo: catálogo novo nunca usa vetor velho.
        path = cache_dir / f"vectors-{cache_key(self.embedder.name, texts)}.npy" if cache_dir else None
        if path and path.exists():
            return np.load(path)
        vectors = self.embedder.embed(texts)
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            np.save(path, vectors)
        return vectors

    def rank(self, query: str) -> list[tuple[int, float]]:
        query_vector = self.embedder.embed([query])[0]
        # Vetores com tamanho 1: o produto escalar é o cosseno.
        scores = self.vectors @ query_vector
        ranked = [(int(i), float(scores[i])) for i in np.argsort(-scores)]
        if self.min_score is None:
            return ranked
        return [(i, score) for i, score in ranked if score >= self.min_score]
