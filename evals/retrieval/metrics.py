from collections import defaultdict

CUTOFFS = (1, 3, 5)


def first_hit(found: list, expected: list) -> int | None:
    for position, item in enumerate(found, start=1):
        if item in expected:
            return position
    return None


def summarize(ranks: list[int | None]) -> dict[str, float]:
    total = len(ranks)
    summary = {f"recall@{k}": sum(1 for r in ranks if r is not None and r <= k) / total for k in CUTOFFS}
    summary["mrr"] = sum(1 / r for r in ranks if r is not None) / total
    return summary


def summarize_by_kind(kinds: list[str], ranks: list[int | None]) -> dict[str, dict[str, float]]:
    groups: dict[str, list[int | None]] = defaultdict(list)
    for kind, rank in zip(kinds, ranks):
        groups[kind].append(rank)
    return {kind: summarize(group) for kind, group in groups.items()}
