import json
import re
from collections.abc import Callable

from evals.assistant.dataset import EvalCase
from evals.assistant.runner import CaseRun

# O (?!\d|[.,]\d) impede que "R$ 1.299,90" seja lido pela metade, como "R$ 1.29" no formato em inglês.
PRICE_PT = re.compile(r"R\$\s?(\d{1,3}(?:\.\d{3})*,\d{2})(?!\d|[.,]\d)")
PRICE_EN = re.compile(r"R\$\s?(\d{1,3}(?:,\d{3})*\.\d{2})(?!\d|[.,]\d)")
MARKDOWN = re.compile(r"\*\*|__|^\s*#|^\s*[-*•]\s|^\s*\d+[.)]\s", re.MULTILINE)
EMOJI = re.compile("[\U0001f300-\U0001faff☀-➿]")
# Ponto seguido de espaço ou fim: "Bluetooth 5.3" e "R$ 1.299,90" não quebram a frase.
SENTENCE_END = re.compile(r"[.!?]+(?=\s|$)")
MAX_SENTENCES = 4
MAX_WORDS = 80


def prices(text: str) -> set[str]:
    found = set(PRICE_PT.findall(text))
    # Em inglês o modelo pode escrever "R$ 1,299.90": volta para o formato das tools antes de comparar.
    found |= {value.replace(",", "_").replace(".", ",").replace("_", ".") for value in PRICE_EN.findall(text)}
    return found


def sentence_count(text: str) -> int:
    return len([part for part in SENTENCE_END.split(text) if part.strip()])


def price_grounded(run: CaseRun, case: EvalCase) -> bool:
    results = json.dumps([step.get("result") for step in run.trace], ensure_ascii=False)
    conversation = " ".join([case.message, *(m.content for m in case.history)])
    return prices(run.answer) <= prices(results) | prices(conversation)


def required_tools(run: CaseRun, case: EvalCase) -> bool:
    return set(case.required_tools) <= {step["tool"] for step in run.trace}


def plain_text(run: CaseRun, case: EvalCase) -> bool:
    return not MARKDOWN.search(run.answer) and not EMOJI.search(run.answer)


def short(run: CaseRun, case: EvalCase) -> bool:
    return sentence_count(run.answer) <= MAX_SENTENCES and len(run.answer.split()) <= MAX_WORDS


CHECKS: dict[str, Callable[[CaseRun, EvalCase], bool]] = {
    "price_grounded": price_grounded,
    "required_tools": required_tools,
    "plain_text": plain_text,
    "short": short,
}


def grade_by_code(run: CaseRun, case: EvalCase) -> tuple[float, dict[str, bool]]:
    # Sem tool obrigatória, a checagem passaria sempre e inflaria a nota: ela só conta onde se aplica.
    names = [name for name in CHECKS if name != "required_tools" or case.required_tools]
    results = {name: CHECKS[name](run, case) for name in names}
    return 10 * sum(results.values()) / len(results), results
