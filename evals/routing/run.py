import json
import sys
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from statistics import mean

from backend.llm import spending
from backend.routing.router import route

DATASET_FILE = Path(__file__).parent / "dataset.json"
RESULTS_DIR = Path(__file__).parent / "results"

ROUTERS: dict[str, Callable[[str], str]] = {
    "haiku": lambda message: route(message, []),
}


def load_dataset(path: Path = DATASET_FILE) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def summarize(results: list[dict]) -> dict:
    # Os dois erros pesam diferente: política mandada ao agente só custa mais; produto mandado à política sai errado.
    return {
        "accuracy": round(sum(r["got"] == r["expected"] for r in results) / len(results), 3),
        "policy_to_agent": sum(r["expected"] == "politica" and r["got"] == "produto" for r in results),
        "product_to_policy": sum(r["expected"] == "produto" and r["got"] == "politica" for r in results),
        "seconds": round(mean(r["seconds"] for r in results), 3),
    }


def main(name: str) -> int:
    if name not in ROUTERS:
        print(f"separador desconhecido: {name}. Disponíveis: {sorted(ROUTERS)}")
        return 1
    spent_before = spending.snapshot("rota")
    results = []
    for case in load_dataset():
        started = time.perf_counter()
        got = ROUTERS[name](case["mensagem"])
        results.append({"id": case["id"], "expected": case["rota"], "got": got,
                        "seconds": round(time.perf_counter() - started, 3)})
        if got != case["rota"]:
            print(f"  errou {case['id']}: esperado {case['rota']}, veio {got} | {case['mensagem']}")
    summary = summarize(results) | {"cost": round((spending.snapshot("rota") - spent_before).cost, 6)}
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / f"{name}-{datetime.now():%Y%m%d-%H%M%S}.json"
    path.write_text(json.dumps({"router": name, "summary": summary, "results": results}, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")
    print("\n| separador | acerto | política → agente | produto → política | tempo médio | custo |")
    print("|---|---|---|---|---|---|")
    print(f"| {name} | {summary['accuracy']:.0%} | {summary['policy_to_agent']} | {summary['product_to_policy']} | "
          f"{summary['seconds']} s | ${summary['cost']:.4f} |")
    print(f"salvo em {path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "haiku"))
