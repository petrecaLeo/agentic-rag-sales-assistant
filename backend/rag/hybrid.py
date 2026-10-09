from collections import defaultdict
from typing import Protocol

from backend.config import RRF_DEPTH, RRF_K


class Index(Protocol):
    def rank(self, query: str) -> list[tuple[int, float]]: ...


class HybridIndex:
    """Reciprocal Rank Fusion: junta rankings pela posição de cada documento, não pela nota."""

    def __init__(self, indexes: list[Index], k: int = RRF_K, depth: int = RRF_DEPTH) -> None:
        self.indexes = indexes
        self.k = k
        self.depth = depth

    def rank(self, query: str) -> list[tuple[int, float]]:
        scores: dict[int, float] = defaultdict(float)
        for index in self.indexes:
            for position, (doc, _) in enumerate(index.rank(query)[: self.depth], start=1):
                scores[doc] += 1 / (self.k + position)
        return sorted(scores.items(), key=lambda item: (-item[1], item[0]))
