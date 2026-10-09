import pytest

from backend.rag.hybrid import HybridIndex
from backend.rag.search import default_policy_search, default_product_search


class Fixed:
    def __init__(self, order: list[int]) -> None:
        self.order = order

    def rank(self, query: str) -> list[tuple[int, float]]:
        return [(doc, 1.0) for doc in self.order]


def test_a_document_found_by_both_beats_one_found_by_a_single_index():
    assert HybridIndex([Fixed([1, 2, 3]), Fixed([4, 2, 5])]).rank("q")[0][0] == 2


def test_score_is_the_sum_of_one_over_k_plus_position():
    ranked = dict(HybridIndex([Fixed([7, 8]), Fixed([8])], k=60).rank("q"))

    assert ranked[8] == pytest.approx(1 / 62 + 1 / 61)
    assert ranked[7] == pytest.approx(1 / 61)


def test_scores_from_each_index_are_ignored():
    class Loud:
        def rank(self, query):
            return [(1, 999.0), (2, 1.0)]

    # Somando notas, o 1 ganharia de longe; pela posição, o 2 aparece nos dois rankings e ganha.
    assert [doc for doc, _ in HybridIndex([Loud(), Fixed([2])]).rank("q")] == [2, 1]


def test_only_the_top_positions_count():
    assert set(dict(HybridIndex([Fixed(list(range(100)))], depth=10).rank("q"))) == set(range(10))


def test_ties_keep_document_order():
    assert [doc for doc, _ in HybridIndex([Fixed([3]), Fixed([1])]).rank("q")] == [1, 3]


def test_empty_when_every_index_is_empty():
    assert HybridIndex([Fixed([]), Fixed([])]).rank("q") == []


def test_the_app_uses_the_hybrid_search():
    assert isinstance(default_product_search().index, HybridIndex)
    assert isinstance(default_policy_search().index, HybridIndex)
