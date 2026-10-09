import json
from datetime import datetime
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"


def summarize(results: list[dict], cost: float) -> dict:
    count = len(results)
    return {
        "code": round(sum(r["code_score"] for r in results) / count, 2),
        "judge": round(sum(r["judge_score"] for r in results) / count, 2),
        "final": round(sum(r["score"] for r in results) / count, 2),
        "ungrounded_prices": sum(1 for r in results if r["checks"].get("price_grounded") is False),
        "errors": sum(1 for r in results if r["error"]),
        "cost": round(cost, 6),
    }


def save_results(version: str, summary: dict, results: list[dict]) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / f"{version}-{datetime.now():%Y%m%d-%H%M}.json"
    data = {"version": version, "date": datetime.now().isoformat(timespec="minutes"), "summary": summary, "results": results}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return path


def print_case(result: dict) -> None:
    failed = [name for name, ok in result["checks"].items() if not ok]
    note = f" | falhou: {', '.join(failed)}" if failed else ""
    error = f" | ERRO: {result['error']}" if result["error"] else ""
    print(f"  {result['id']:22} código {result['code_score']:4.1f} | juiz {result['judge_score']:2} | final {result['score']:4.1f}{note}{error}")


def print_report(reports: dict[str, dict]) -> None:
    print("\n| versão | código | juiz | final | preços sem fonte | erros | custo |")
    print("|---|---|---|---|---|---|---|")
    for version, summary in reports.items():
        print(f"| {version} | {summary['code']} | {summary['judge']} | **{summary['final']}** | "
              f"{summary['ungrounded_prices']} | {summary['errors']} | ${summary['cost']:.4f} |")
