from typing import Literal

import anthropic
from anthropic.types import MessageParam
from pydantic import BaseModel

from backend.assistant.history_text import recent_conversation
from backend.config import CONTEXT_MESSAGE_CHARS, CONTEXT_MESSAGES, HAIKU, ROUTER_MAX_TOKENS
from backend.llm import get_client, log_cost
from backend.prompts.router import ROUTER_PROMPT, router_input

Route = Literal["politica", "produto"]
# O agente também sabe consultar a política: mandar para ele por engano só custa mais.
SAFE_ROUTE: Route = "produto"


class RouteChoice(BaseModel):
    rota: Route


def route(message: str, history: list[MessageParam]) -> Route:
    conversation = recent_conversation(history, CONTEXT_MESSAGES, CONTEXT_MESSAGE_CHARS)
    try:
        response = get_client().messages.parse(
            model=HAIKU,
            max_tokens=ROUTER_MAX_TOKENS,
            system=ROUTER_PROMPT,
            messages=[{"role": "user", "content": router_input(message, conversation)}],
            output_format=RouteChoice,
            thinking={"type": "disabled"},
        )
    except (anthropic.APIError, ValueError) as error:
        print(f"[rota] falhou, vai para o agente: {error!r}")
        return SAFE_ROUTE
    log_cost("rota", HAIKU, response)
    return response.parsed_output.rota if response.parsed_output else SAFE_ROUTE
