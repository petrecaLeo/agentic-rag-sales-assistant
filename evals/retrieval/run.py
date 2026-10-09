import json
import sys
from datetime import datetime
from pathlib import Path

from backend.catalog.store import default_catalog
from backend.rag.documents import load_policy_chunks
from backend.rag.search import METHODS, PolicySearch, ProductSearch, SearchMethod
from evals.retrieval.dataset import RetrievalCase, load_dataset
from evals.retrieval.metrics import CUTOFFS, first_hit, summarize, summarize_by_kind

RESULTS_DIR = Path(__file__).parent / "results"
TOP_K = max(CUTOFFS)


def run_method(method: SearchMethod, cases: list[RetrievalCase]) -> list[dict]:
    products = ProductSearch(default_catalog().products, method.products)
    policy = PolicySearch(load_policy_chunks(), method.policy)
    results = []
    for case in cases:
        if case.is_policy:
            found = [chunk.tema for chunk in policy.search(case.consulta, TOP_K)]
        else:
            found = [product.id for product in products.search(case.consulta, TOP_K)]
        results.append({"id": case.id, "tipo": case.tipo, "encontrado": found, "posicao": first_hit(found, case.esperado)})
    return results


def percent(value: float) -> str:
    return f"{value * 100:.0f}%"


def print_report(report: dict) -> None:
    metrics = [f"recall@{k}" for k in CUTOFFS] + ["mrr"]
    print("| método | " + " | ".join(metrics) + " |")
    print("|---" * (len(metrics) + 1) + "|")
    for method, data in report.items():
        cells = [percent(v) if k != "mrr" else f"{v:.2f}" for k, v in data["geral"].items()]
        print(f"| {method} | " + " | ".join(cells) + " |")

    kinds = list(next(iter(report.values()))["por_tipo"])
    print("\nrecall@3 por tipo de consulta:\n")
    print("| método | " + " | ".join(kinds) + " |")
    print("|---" * (len(kinds) + 1) + "|")
    for method, data in report.items():
        print(f"| {method} | " + " | ".join(percent(data["por_tipo"][k]["recall@3"]) for k in kinds) + " |")

    for method, data in report.items():
        misses = [r["id"] for r in data["casos"] if r["posicao"] is None]
        print(f"\n{method}: {len(misses)} sem acerto no top {TOP_K}: {', '.join(misses) or 'nenhum'}")


def main(methods: list[str]) -> int:
    unknown = [m for m in methods if m not in METHODS]
    if unknown:
        print(f"métodos desconhecidos: {unknown}. Disponíveis: {list(METHODS)}")
        return 1
    cases = load_dataset()
    report = {}
    for method in methods:
        results = run_method(METHODS[method], cases)
        ranks = [r["posicao"] for r in results]
        report[method] = {
            "geral": summarize(ranks),
            "por_tipo": summarize_by_kind([r["tipo"] for r in results], ranks),
            "casos": results,
        }
    print_report(report)
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / f"retrieval-{datetime.now():%Y%m%d-%H%M}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nresultado salvo em {path.relative_to(Path.cwd()) if path.is_relative_to(Path.cwd()) else path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or list(METHODS)))
