import os
from collections import defaultdict
from dataclasses import dataclass, field, replace

from anthropic import Anthropic
from anthropic.types import Message

from backend.config import CACHE_READ_FACTOR, CACHE_WRITE_FACTOR, PRICES


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
class Usage:
    calls: int = 0
    cost: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read: int = 0
    cache_write: int = 0

    def __add__(self, other: "Usage") -> "Usage":
        return Usage(*(a + b for a, b in zip(vars(self).values(), vars(other).values())))

    def __sub__(self, other: "Usage") -> "Usage":
        return Usage(*(a - b for a, b in zip(vars(self).values(), vars(other).values())))


@dataclass
class Spending:
    by_label: defaultdict[str, Usage] = field(default_factory=lambda: defaultdict(Usage))

    @property
    def total(self) -> float:
        return sum(usage.cost for usage in self.by_label.values())

    def snapshot(self, *labels: str) -> Usage:
        return sum((replace(self.by_label[label]) for label in labels), Usage())


spending = Spending()


def call_usage(model: str, message: Message) -> Usage:
    input_price, output_price = PRICES[model]
    usage = message.usage
    cache_read = usage.cache_read_input_tokens or 0
    cache_write = usage.cache_creation_input_tokens or 0
    cost = (
        usage.input_tokens * input_price
        + cache_write * input_price * CACHE_WRITE_FACTOR
        + cache_read * input_price * CACHE_READ_FACTOR
        + usage.output_tokens * output_price
    ) / 1_000_000
    return Usage(1, cost, usage.input_tokens, usage.output_tokens, cache_read, cache_write)


def log_cost(label: str, model: str, message: Message) -> float:
    usage = call_usage(model, message)
    cache = f" | cache: {usage.cache_read} lidos, {usage.cache_write} gravados" if usage.cache_read or usage.cache_write else ""
    print(f"[{label}] tokens: {usage.input_tokens} in / {usage.output_tokens} out{cache} | cost: ${usage.cost:.6f}")
    spending.by_label[label] += usage
    if message.stop_reason == "max_tokens":
        print(f"[{label}] aviso: resposta cortada pelo max_tokens")
    return usage.cost
