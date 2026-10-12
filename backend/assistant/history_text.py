from anthropic.types import MessageParam

ROLE_NAMES = {"user": "cliente", "assistant": "assistente"}


def message_text(message: MessageParam) -> str:
    content = message["content"]
    if isinstance(content, str):
        return content
    # O histórico mistura dicts e blocos do SDK: as respostas do agente são guardadas como vieram da API.
    parts = []
    for block in content:
        if isinstance(block, dict):
            if block.get("type") == "text":
                parts.append(block["text"])
        elif block.type == "text":
            parts.append(block.text)
    return " ".join(parts)


def recent_conversation(messages: list[MessageParam], limit: int, max_chars: int) -> str:
    turns = [(message["role"], message_text(message).strip()) for message in messages]
    lines = [f"{ROLE_NAMES[role]}: {text[:max_chars]}" for role, text in turns if text][-limit:]
    return "\n".join(lines)
