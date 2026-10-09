import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.schemas import Language
from backend.tools.definitions import TOOL_INPUTS

DATASET_FILE = Path(__file__).parent / "dataset.json"


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class EvalCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    language: Language = "pt"
    history: list[HistoryMessage] = []
    message: str
    required_tools: list[str]
    tem_que: str = Field(min_length=20)
    nao_pode: str = Field(min_length=10)

    @model_validator(mode="after")
    def consistent(self) -> "EvalCase":
        unknown = set(self.required_tools) - set(TOOL_INPUTS)
        if unknown:
            raise ValueError(f"tools que não existem: {unknown}")
        roles = [m.role for m in self.history]
        if roles != ["user", "assistant"] * (len(roles) // 2):
            raise ValueError("o histórico alterna cliente e assistente e termina no assistente")
        return self


def load_dataset(path: Path = DATASET_FILE) -> list[EvalCase]:
    cases = [EvalCase.model_validate(item) for item in json.loads(path.read_text(encoding="utf-8"))]
    ids = [case.id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("ids repetidos no dataset")
    return cases
