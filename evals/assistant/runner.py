import time
from dataclasses import dataclass, field

import anthropic

from backend.assistant.profiles import Profile
from backend.assistant.reply import reply
from backend.llm import Usage, spending
from backend.sessions import Session
from evals.assistant.dataset import EvalCase

SERVING_LABELS = ("assistant", "rota", "politica")


@dataclass
class CaseRun:
    answer: str = ""
    trace: list[dict] = field(default_factory=list)
    error: str | None = None
    route: str | None = None
    citations: list[str] = field(default_factory=list)
    seconds: float = 0.0
    first_word_seconds: float | None = None
    usage: Usage = field(default_factory=Usage)


def run_case(case: EvalCase, profile: Profile) -> CaseRun:
    session = Session(id="eval", last_seen=0, messages=[m.model_dump() for m in case.history])
    run = CaseRun()
    before = spending.snapshot(*SERVING_LABELS)
    started = time.perf_counter()
    try:
        for event in reply(session, case.message, case.language, profile):
            if event["type"] == "text":
                if run.first_word_seconds is None:
                    run.first_word_seconds = time.perf_counter() - started
                run.answer += event["text"]
            elif event["type"] == "tool_call":
                # Como na tela: o texto antes de uma tool é narração, e a resposta é o que vem depois da última.
                run.answer = ""
                run.first_word_seconds = None
                run.trace.append({"tool": event["name"], "input": event["input"]})
            elif event["type"] == "tool_result":
                run.trace[-1] |= {"ok": event["ok"], "result": event["data"]}
            elif event["type"] == "route":
                run.route = event["name"]
            elif event["type"] == "citations":
                run.citations = event["items"]
            elif event["type"] == "error":
                run.error = event["code"]
    except anthropic.APIError as error:
        run.error = f"api: {error.__class__.__name__}"
    run.seconds = time.perf_counter() - started
    run.usage = spending.snapshot(*SERVING_LABELS) - before
    run.answer = run.answer.strip()
    return run
