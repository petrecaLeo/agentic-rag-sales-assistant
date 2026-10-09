import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

DATASET_FILE = Path(__file__).parent / "dataset.json"

CaseKind = Literal["nome", "necessidade", "ingles", "politica"]


class RetrievalCase(BaseModel):
    id: str
    tipo: CaseKind
    consulta: str
    esperado: list[int | str] = Field(min_length=1)

    @property
    def is_policy(self) -> bool:
        return self.tipo == "politica"


def load_dataset(path: Path = DATASET_FILE) -> list[RetrievalCase]:
    cases = [RetrievalCase.model_validate(item) for item in json.loads(path.read_text(encoding="utf-8"))]
    ids = [case.id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("ids repetidos no dataset")
    return cases
