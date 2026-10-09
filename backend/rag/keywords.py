from backend.rag.text import words

MIN_WORD_LENGTH = 4


class KeywordIndex:
    def __init__(self, texts: list[str]) -> None:
        self.docs = [set(words(text)) for text in texts]

    def rank(self, query: str) -> list[tuple[int, float]]:
        terms = {word for word in words(query) if len(word) >= MIN_WORD_LENGTH}
        hits = [(index, float(len(terms & doc))) for index, doc in enumerate(self.docs)]
        return sorted([hit for hit in hits if hit[1] > 0], key=lambda hit: -hit[1])
