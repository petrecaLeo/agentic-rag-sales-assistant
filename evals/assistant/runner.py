from dataclasses import dataclass, field

import anthropic

from backend.assistant.loop import stream_reply
from backend.sessions import Session
from evals.assistant.dataset import EvalCase


@dataclass
class CaseRun:
    answer: str = ""
    trace: list[dict] = field(default_factory=list)
    error: str | None = None


def run_case(case: EvalCase, version: str) -> CaseRun:
    session = Session(id="eval", last_seen=0, messages=[m.model_dump() for m in case.history])
    run = CaseRun()
    try:
        for event in stream_reply(session, case.message, case.language, version):
            if event["type"] == "text":
                run.answer += event["text"]
            elif event["type"] == "tool_call":
                # Como na tela: o texto antes de uma tool é narração, e a resposta é o que vem depois da última.
                run.answer = ""
                run.trace.append({"tool": event["name"], "input": event["input"]})
            elif event["type"] == "tool_result":
                run.trace[-1] |= {"ok": event["ok"], "result": event["data"]}
            elif event["type"] == "error":
                run.error = event["code"]
    except anthropic.APIError as error:
        run.error = f"api: {error.__class__.__name__}"
    run.answer = run.answer.strip()
    return run
