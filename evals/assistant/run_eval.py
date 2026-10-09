import sys

from backend.llm import spending
from backend.prompts.assistant import ACTIVE_VERSION, ASSISTANT_PROMPTS
from evals.assistant.checks import grade_by_code
from evals.assistant.dataset import EvalCase, load_dataset
from evals.assistant.judge import JudgeFailed, grade_by_model
from evals.assistant.report import print_case, print_report, save_results, summarize
from evals.assistant.runner import run_case


def evaluate(case: EvalCase, version: str) -> dict:
    run = run_case(case, version)
    result = {"id": case.id, "answer": run.answer, "trace": run.trace, "error": run.error}
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


def main(versions: list[str], only: list[str] | None = None) -> int:
    unknown = [v for v in versions if v not in ASSISTANT_PROMPTS]
    if unknown:
        print(f"versões desconhecidas: {unknown}. Disponíveis: {sorted(ASSISTANT_PROMPTS)}")
        return 1
    cases = [c for c in load_dataset() if not only or c.id in only]
    reports = {}
    for version in versions:
        print(f"\n== {version} ({len(cases)} casos)")
        spent_before = spending.total
        results = []
        for case in cases:
            results.append(evaluate(case, version))
            print_case(results[-1])
        reports[version] = summarize(results, spending.total - spent_before)
        print(f"  salvo em {save_results(version, reports[version], results).name}")
    print_report(reports)
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    only = [a.removeprefix("--caso=") for a in args if a.startswith("--caso=")]
    versions = [a for a in args if not a.startswith("--")] or [ACTIVE_VERSION]
    sys.exit(main(versions, only))
