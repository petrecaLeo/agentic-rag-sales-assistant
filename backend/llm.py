import os
from dataclasses import dataclass

from anthropic import Anthropic
from anthropic.types import Message

from backend.config import PRICES


class MissingApiKey(RuntimeError):
    pass


# Criado no primeiro uso: sem chave, o servidor e os testes sobem, e o erro aparece na tela.
_client: Anthropic | None = None


def get_client() -> Anthropic:
    global _client
    if _client is None:
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise MissingApiKey("Falta a ANTHROPIC_API_KEY. Copie o .env.example para .env e coloque a sua chave.")
        _client = Anthropic()
    return _client


@dataclass
class Spending:
    total: float = 0.0


spending = Spending()


def log_cost(label: str, model: str, message: Message) -> float:
    input_price, output_price = PRICES[model]
    usage = message.usage
    cost = (usage.input_tokens * input_price + usage.output_tokens * output_price) / 1_000_000
    print(f"[{label}] tokens: {usage.input_tokens} in / {usage.output_tokens} out | cost: ${cost:.6f}")
    spending.total += cost
    if message.stop_reason == "max_tokens":
        print(f"[{label}] aviso: resposta cortada pelo max_tokens")
    return cost
