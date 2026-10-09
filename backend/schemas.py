from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from backend.config import MAX_USER_MESSAGE_CHARS

Language = Literal["pt", "en"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ChatRequest(StrictModel):
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_USER_MESSAGE_CHARS)]
    session_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{32}$")
    language: Language = "pt"
