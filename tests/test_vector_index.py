import numpy as np
import pytest

from backend.rag.embeddings import default_embedder, unit_rows
from backend.rag.vector_index import VectorIndex, cache_key
from tests.conftest import HashEmbedder

TEXTS = ["fone esportivo com gancho", "teclado mecânico", "notebook para jogos"]


def test_nearest_text_comes_first_and_every_text_is_ranked():
    index = VectorIndex(TEXTS, HashEmbedder())
    ranked = index.rank("fone com gancho")

    assert ranked[0][0] == 0
    assert sorted(i for i, _ in ranked) == [0, 1, 2]
    assert [score for _, score in ranked] == sorted((score for _, score in ranked), reverse=True)


def test_vectors_are_cached_and_reused(tmp_path):
    embedder = HashEmbedder()
    VectorIndex(TEXTS, embedder, tmp_path)
    VectorIndex(TEXTS, embedder, tmp_path)

    assert embedder.calls == 1
    assert len(list(tmp_path.glob("vectors-*.npy"))) == 1


def test_changed_texts_never_use_old_vectors(tmp_path):
    VectorIndex(TEXTS, HashEmbedder(), tmp_path)
    VectorIndex([*TEXTS, "mouse sem fio"], HashEmbedder(), tmp_path)

    assert len(list(tmp_path.glob("vectors-*.npy"))) == 2


def test_cache_key_depends_on_model_and_texts():
    assert cache_key("a", TEXTS) != cache_key("b", TEXTS)
    assert cache_key("a", ["x y"]) != cache_key("a", ["x", "y"])


def test_min_score_drops_distant_texts():
    ranked = VectorIndex(TEXTS, HashEmbedder(), min_score=0.5).rank("fone com gancho")

    assert [i for i, _ in ranked] == [0]
    assert VectorIndex(TEXTS, HashEmbedder(), min_score=0.99).rank("geladeira") == []


def test_unit_rows():
    rows = unit_rows(np.array([[3.0, 4.0], [0.0, 0.0]]))

    assert np.allclose(rows, [[0.6, 0.8], [0.0, 0.0]])


def test_tests_never_load_the_real_model():
    with pytest.raises(RuntimeError):
        default_embedder()
