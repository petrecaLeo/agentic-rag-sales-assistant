from anthropic.types import Message

from backend.config import HAIKU, SONNET
from backend.llm import Spending, Usage, call_usage


def message(input_tokens: int, output_tokens: int, cache_read: int = 0, cache_write: int = 0) -> Message:
    return Message.model_validate({
        "id": "m", "type": "message", "role": "assistant", "model": SONNET, "content": [],
        "stop_reason": "end_turn", "stop_sequence": None,
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens,
                  "cache_read_input_tokens": cache_read, "cache_creation_input_tokens": cache_write},
    })


def test_cost_without_cache():
    assert call_usage(SONNET, message(1000, 100)).cost == (1000 * 2 + 100 * 10) / 1_000_000


def test_cache_write_costs_more_and_cache_read_costs_a_tenth():
    usage = call_usage(SONNET, message(10, 100, cache_read=2000, cache_write=1000))

    assert usage.cache_read == 2000 and usage.cache_write == 1000
    assert usage.cost == (10 * 2 + 1000 * 2 * 1.25 + 2000 * 2 * 0.1 + 100 * 10) / 1_000_000


def test_haiku_prices():
    assert call_usage(HAIKU, message(1000, 100)).cost == (1000 * 0.10 + 100 * 0.50) / 1_000_000


def test_spending_adds_by_label_and_snapshots_are_copies():
    spending = Spending()
    spending.by_label["assistant"] += Usage(1, 0.5, 10, 1)
    before = spending.snapshot("assistant")
    spending.by_label["assistant"] += Usage(1, 0.25, 20, 2)
    spending.by_label["juiz"] += Usage(1, 0.1)

    assert (spending.snapshot("assistant") - before) == Usage(1, 0.25, 20, 2)
    assert spending.snapshot("assistant", "juiz").calls == 3
    assert round(spending.total, 2) == 0.85
