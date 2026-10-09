import json

import pytest

from backend.catalog.models import Product
from backend.config import HELPER_MODEL
from data import generate_catalog
from data.generator.describe import DescriptionFailed, describe_batch
from tests.conftest import Reply, text

GOOD = "Fone sem fio leve e confortável, com bateria para o dia inteiro, ideal para academia, corrida e chamadas no caminho."


def products(*ids: int, descricao: str = "") -> list[Product]:
    return [
        Product(id=i, nome=f"Fone {i}", categoria="fones", marca="Pulse", preco=9990, estoque=1,
                atributos={"tipo": "sem fio"}, descricao=descricao)
        for i in ids
    ]


def written(*ids: int, descricao: str = GOOD) -> Reply:
    payload = {"descricoes": [{"id": i, "descricao": descricao} for i in ids]}
    return Reply([text(json.dumps(payload, ensure_ascii=False))])


def test_describes_a_batch_with_structured_output(fake_api):
    fake_api.queue(written(1, 2))

    assert describe_batch(products(1, 2)) == {1: GOOD, 2: GOOD}
    body = fake_api.requests[0]
    assert body["model"] == HELPER_MODEL
    assert body["output_config"]["format"]["type"] == "json_schema"
    assert "messages" in body and body["messages"][-1]["role"] == "user"


@pytest.mark.parametrize(
    "bad",
    [
        written(1),
        written(1, 2, descricao="Curto demais."),
        written(1, 2, descricao=GOOD + " Por apenas R$ 99,90."),
        written(1, 2, descricao=" ".join(["palavra"] * 80)),
        Reply([text("isto não é JSON")]),
    ],
)
def test_bad_batch_is_retried_once(fake_api, bad):
    fake_api.queue(bad, written(1, 2))

    assert describe_batch(products(1, 2)) == {1: GOOD, 2: GOOD}
    assert len(fake_api.requests) == 2


def test_gives_up_after_two_bad_attempts(fake_api):
    fake_api.queue(written(1), written(1))

    with pytest.raises(DescriptionFailed):
        describe_batch(products(1, 2))


def test_rerun_only_fills_missing_descriptions(fake_api, tmp_path):
    path = tmp_path / "catalog.json"
    done = products(1, 2, descricao="Já escrita, não pode mudar.")
    generate_catalog.save([*done, *products(3, 4)], path)
    fake_api.queue(written(3, 4))

    assert generate_catalog.main(path) == 0

    saved = {item["id"]: item["descricao"] for item in json.loads(path.read_text(encoding="utf-8"))}
    assert saved == {1: "Já escrita, não pode mudar.", 2: "Já escrita, não pode mudar.", 3: GOOD, 4: GOOD}
    assert generate_catalog.main(path) == 0
    assert len(fake_api.requests) == 1
