from backend.rag.bm25 import BM25Index
from backend.rag.keywords import KeywordIndex


def top(index, query: str) -> int | None:
    ranked = index.rank(query)
    return ranked[0][0] if ranked else None


def test_rare_word_weighs_more_than_a_repeated_common_word():
    index = BM25Index(["fone fone", "gancho", "fone", "fone"])

    assert top(index, "fone gancho") == 1


def test_repeating_a_word_has_diminishing_returns():
    index = BM25Index(["bateria", "bateria bateria bateria bateria bateria bateria", "tela", "cabo"])
    ranked = dict(index.rank("bateria"))

    assert ranked[1] < ranked[0] * 2


def test_long_documents_are_penalized():
    short = "fone esportivo"
    long = "fone esportivo " + " ".join(f"palavra{i}" for i in range(30))
    index = BM25Index([long, short, "teclado", "mouse"])

    assert top(index, "esportivo") == 1


def test_accents_and_case_do_not_matter():
    index = BM25Index(["Condução óssea", "Intra-auricular", "Over-ear"])

    assert top(index, "CONDUCAO OSSEA") == 0


def test_short_words_and_numbers_count():
    index = BM25Index(["Vetor G15 16 GB", "Vetor G15 32 GB", "Vetor 15 8 GB"])

    assert top(index, "vetor g15 32") == 1


def test_keyword_baseline_ignores_short_words():
    index = KeywordIndex(["Vetor G15 16 GB", "Vetor G15 32 GB"])

    assert index.rank("vetor g15 32") == [(0, 1.0), (1, 1.0)]


def test_no_shared_word_means_no_result():
    assert BM25Index(["fone", "cabo"]).rank("geladeira") == []
