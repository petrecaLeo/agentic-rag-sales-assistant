import random

SEED = 2026


def draw_price(rng: random.Random, low: float, high: float) -> int:
    value = rng.uniform(low, high)
    step = 10 if value >= 100 else 1
    return round(value / step) * step * 100 - 10


def draw_stock(rng: random.Random) -> int:
    return 0 if rng.random() < 0.1 else rng.randint(1, 60)


def thousands(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def decimal(value: float) -> str:
    return f"{value:.1f}".replace(".", ",")
