from anthropic.types import MessageParam

from backend.assistant.profiles import Profile
from backend.prompts.assistant import build_system
from backend.tools.definitions import TOOLS


def assistant_params(messages: list[MessageParam], language: str, profile: Profile) -> dict:
    params = {
        "model": profile.model,
        "max_tokens": profile.max_tokens,
        "system": build_system(language, profile.prompt),
        "messages": messages,
        "tools": TOOLS,
        "thinking": profile.thinking,
        "output_config": {"effort": profile.effort},
    }
    if profile.cache:
        # Dois pontos: o do system guarda tools + system, iguais para todas as conversas;
        # o do topo marca o fim da conversa, que a próxima volta do agente relê.
        params["system"] = [{"type": "text", "text": params["system"], "cache_control": {"type": "ephemeral"}}]
        params["cache_control"] = {"type": "ephemeral"}
    return params
