from pydantic import BaseModel, Field

from backend.config import HELPER_MODEL, JUDGE_MAX_TOKENS
from backend.llm import get_client, log_cost
from evals.assistant.dataset import EvalCase
from evals.assistant.judge_prompt import build_judge_prompt
from evals.assistant.runner import CaseRun


class Verdict(BaseModel):
    reasoning: str
    score: int = Field(ge=1, le=10)


class JudgeFailed(Exception):
    pass


def grade_by_model(case: EvalCase, run: CaseRun, attempts: int = 2) -> Verdict:
    for _ in range(attempts):
        try:
            response = get_client().messages.parse(
                model=HELPER_MODEL,
                max_tokens=JUDGE_MAX_TOKENS,
                messages=[{"role": "user", "content": build_judge_prompt(case, run)}],
                output_format=Verdict,
                # O Haiku 5.5 recusa temperature com erro 400 e pensa por padrão; o juiz só precisa da nota.
                thinking={"type": "disabled"},
            )
        except ValueError as error:
            print(f"[juiz] {case.id}: resposta fora do formato ({str(error).splitlines()[0]})")
            continue
        log_cost("juiz", HELPER_MODEL, response)
        return response.parsed_output
    raise JudgeFailed(case.id)
