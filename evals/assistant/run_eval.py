import sys

from backend.assistant.profiles import ACTIVE_PROFILE, PROFILES, Profile
from backend.llm import spending
from backend.rag.search import default_policy_search, default_product_search
from backend.tools.mcp_client import mcp_tools
from evals.assistant.checks import grade_by_code
from evals.assistant.dataset import EvalCase, load_dataset
from evals.assistant.judge import JudgeFailed, grade_by_model
from evals.assistant.report import print_case, print_report, save_results, summarize
from evals.assistant.runner import run_case


def evaluate(case: EvalCase, profile: Profile) -> dict:
    run = run_case(case, profile)
    result = {
        "id": case.id,
        "group": case.group,
        "answer": run.answer,
        "trace": run.trace,
        "error": run.error,
        "route": run.route,
        "citations": run.citations,
        "seconds": round(run.seconds, 2),
        "first_word_seconds": None if run.first_word_seconds is None else round(run.first_word_seconds, 2),
        "usage": vars(run.usage) | {"cost": round(run.usage.cost, 6)},
    }
    if run.error:
        return result | {"checks": {}, "code_score": 0.0, "judge_score": 1, "judge_reasoning": "", "score": 0.0}
    code_score, checks = grade_by_code(run, case)
    try:
        verdict = grade_by_model(case, run)
    except JudgeFailed:
        return result | {"checks": checks, "code_score": code_score, "judge_score": 1,
                         "judge_reasoning": "o juiz falhou", "score": 0.0, "error": "judge_failed"}
    return result | {
        "checks": checks,
        "code_score": code_score,
        "judge_score": verdict.score,
        "judge_reasoning": verdict.reasoning,
        "score": (code_score + verdict.score) / 2,
    }


def main(names: list[str], only: list[str] | None = None) -> int:
    unknown = [name for name in names if name not in PROFILES]
    if unknown:
        print(f"perfis desconhecidos: {unknown}. Disponíveis: {sorted(PROFILES)}")
        return 1
    cases = [c for c in load_dataset() if not only or c.id in only]
    # Carrega tudo antes do primeiro caso, como o app faz ao subir: o tempo medido é só o da resposta.
    default_product_search()
    default_policy_search()
    if any(PROFILES[name].tools == "mcp" for name in names):
        mcp_tools()
    reports = []
    for name in names:
        print(f"\n== {name} ({len(cases)} casos)")
        judge_before = spending.snapshot("juiz")
        results = []
        for case in cases:
            results.append(evaluate(case, PROFILES[name]))
            print_case(results[-1])
        summary = summarize(results, (spending.snapshot("juiz") - judge_before).cost)
        reports.append((name, summary))
        print(f"  salvo em {save_results(name, PROFILES[name], summary, results).name}")
    print_report(reports)
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    only = [a.removeprefix("--caso=") for a in args if a.startswith("--caso=")]
    names = [a for a in args if not a.startswith("--")] or [ACTIVE_PROFILE]
    sys.exit(main(names, only))
