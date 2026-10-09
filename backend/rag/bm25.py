import math
from collections import Counter

from backend.rag.text import words


class BM25Index:
    def __init__(self, texts: list[str], k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.docs = [Counter(words(text)) for text in texts]
        self.lengths = [sum(doc.values()) for doc in self.docs]
        self.average_length = sum(self.lengths) / len(self.docs)
        document_frequency = Counter(term for doc in self.docs for term in doc)
        total = len(self.docs)
        self.idf = {
            term: math.log(1 + (total - count + 0.5) / (count + 0.5)) for term, count in document_frequency.items()
        }

    def score(self, query_terms: list[str], index: int) -> float:
        doc = self.docs[index]
        length_factor = 1 - self.b + self.b * self.lengths[index] / self.average_length
        total = 0.0
        for term in query_terms:
            frequency = doc.get(term, 0)
            if frequency:
                total += self.idf[term] * frequency * (self.k1 + 1) / (frequency + self.k1 * length_factor)
        return total

    def rank(self, query: str) -> list[tuple[int, float]]:
        query_terms = words(query)
        scores = [(index, self.score(query_terms, index)) for index in range(len(self.docs))]
        return sorted([item for item in scores if item[1] > 0], key=lambda item: -item[1])
