import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from statistics import mean

from backend.assistant.profiles import Profile

RESULTS_DIR = Path(__file__).parent / "results"


def summarize(all_results: list[dict], judge_cost: float) -> dict:
    # As métricas principais usam só os 15 casos originais, para continuarem comparáveis com as etapas 1 e 2.
    originals = [r for r in all_results if r.get("group", "original") == "original"] or all_results
    extras = [r for r in all_results if r.get("group") == "fora_do_roteiro"]
    return metrics(originals) | {
        "extra_final": round(mean(r["score"] for r in extras), 2) if extras else None,
        "extra_below_8": [r["id"] for r in extras if r["score"] < 8],
        "judge_cost": round(judge_cost, 6),
        "cost": round(sum(r["usage"]["cost"] for r in all_results) + judge_cost, 6),
    }


def metrics(results: list[dict]) -> dict:
    count = len(results)
    first_words = [r["first_word_seconds"] for r in results if r["first_word_seconds"] is not None]
    serving_cost = sum(r["usage"]["cost"] for r in results)
    return {
        "code": round(sum(r["code_score"] for r in results) / count, 2),
        "judge": round(sum(r["judge_score"] for r in results) / count, 2),
        "final": round(sum(r["score"] for r in results) / count, 2),
        "ungrounded_prices": sum(1 for r in results if r["checks"].get("price_grounded") is False),
        "errors": sum(1 for r in results if r["error"]),
        "cost_per_question": round(serving_cost / count, 6),
        "seconds": round(mean(r["seconds"] for r in results), 2),
        "first_word_seconds": round(mean(first_words), 2) if first_words else None,
        "calls_per_question": round(mean(r["usage"]["calls"] for r in results), 2),
        "cache_read": sum(r["usage"]["cache_read"] for r in results),
        "cache_write": sum(r["usage"]["cache_write"] for r in results),
    }


def save_results(name: str, profile: Profile, summary: dict, results: list[dict]) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / f"{name}-{datetime.now():%Y%m%d-%H%M%S}.json"
    data = {
        "profile": name,
        "settings": asdict(profile),
        "date": datetime.now().isoformat(timespec="minutes"),
        "summary": summary,
        "results": results,
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return path


def print_case(result: dict) -> None:
    failed = [name for name, ok in result["checks"].items() if not ok]
    note = f" | falhou: {', '.join(failed)}" if failed else ""
    error = f" | ERRO: {result['error']}" if result["error"] else ""
    usage = result["usage"]
    print(f"  {result['id']:22} código {result['code_score']:4.1f} | juiz {result['judge_score']:2} | "
          f"final {result['score']:4.1f} | {result['seconds']:5.1f} s | {usage['calls']} chamadas | "
          f"${usage['cost']:.4f}{note}{error}")


def print_report(reports: list[tuple[str, dict]]) -> None:
    print("\n| perfil | código | juiz | final | preços sem fonte | erros | custo/pergunta | tempo | 1ª palavra | chamadas | cache lido | fora do roteiro | custo total |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for name, s in reports:
        first_word = "-" if s["first_word_seconds"] is None else f"{s['first_word_seconds']} s"
        extra = "-" if s.get("extra_final") is None else f"{s['extra_final']} (abaixo de 8: {', '.join(s['extra_below_8']) or 'nenhum'})"
        print(f"| {name} | {s['code']} | {s['judge']} | **{s['final']}** | {s['ungrounded_prices']} | {s['errors']} | "
              f"${s['cost_per_question']:.4f} | {s['seconds']} s | {first_word} | {s['calls_per_question']} | "
              f"{s['cache_read']} | {extra} | ${s['cost']:.4f} |")
