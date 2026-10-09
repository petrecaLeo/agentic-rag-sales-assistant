from backend.catalog.store import default_catalog
from backend.rag.documents import load_policy_chunks
from evals.retrieval.dataset import load_dataset
from evals.retrieval.metrics import first_hit, summarize, summarize_by_kind

CASES = load_dataset()


def test_expected_answers_exist():
    catalog = default_catalog()
    topics = {chunk.tema for chunk in load_policy_chunks()}
    for case in CASES:
        if case.is_policy:
            assert set(case.esperado) <= topics, case.id
        else:
            assert all(isinstance(i, int) and catalog.get(i) for i in case.esperado), case.id


def test_every_kind_is_covered():
    assert {case.tipo for case in CASES} == {"nome", "necessidade", "ingles", "politica"}


def test_first_hit_is_one_based():
    assert first_hit([7, 3, 9], [9, 3]) == 2
    assert first_hit([7], [9]) is None


def test_summary():
    summary = summarize([1, 3, None, 2])

    assert summary == {"recall@1": 0.25, "recall@3": 0.75, "recall@5": 0.75, "mrr": (1 + 1 / 3 + 1 / 2) / 4}


def test_summary_by_kind():
    by_kind = summarize_by_kind(["nome", "nome", "politica"], [1, None, 2])

    assert by_kind["nome"]["recall@1"] == 0.5
    assert by_kind["politica"]["mrr"] == 0.5
