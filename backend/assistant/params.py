from anthropic.types import MessageParam

from backend.config import ASSISTANT_MAX_TOKENS, ASSISTANT_MODEL
from backend.prompts.assistant import ACTIVE_VERSION, build_system
from backend.tools.definitions import TOOLS


def assistant_params(messages: list[MessageParam], language: str, version: str = ACTIVE_VERSION) -> dict:
    return {
        "model": ASSISTANT_MODEL,
        "max_tokens": ASSISTANT_MAX_TOKENS,
        "system": build_system(language, version),
        "messages": messages,
        "tools": TOOLS,
        # O "disabled" dá erro 400 no Sonnet 5.5; este é o ajuste mais baixo.
        "thinking": {"type": "between_tools"},
        "output_config": {"effort": "low"},
    }
