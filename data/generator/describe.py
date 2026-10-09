from pydantic import BaseModel

from backend.catalog.models import Product
from backend.config import DESCRIPTION_MAX_TOKENS, DESCRIPTION_MAX_WORDS, HELPER_MODEL
from backend.llm import get_client, log_cost
from backend.prompts.catalog import build_description_prompt

MIN_WORDS = 15
# O modelo conta palavras com folga; acima disso, o texto passa do que o embedding consegue ler.
WORD_TOLERANCE = 10


class WrittenDescription(BaseModel):
    id: int
    descricao: str


class WrittenBatch(BaseModel):
    descricoes: list[WrittenDescription]


class DescriptionFailed(Exception):
    pass


def description_problems(batch: list[Product], written: WrittenBatch) -> list[str]:
    problems = []
    expected = sorted(p.id for p in batch)
    received = sorted(d.id for d in written.descricoes)
    if received != expected:
        problems.append(f"ids {received}, esperados {expected}")
    for description in written.descricoes:
        words = len(description.descricao.split())
        if not MIN_WORDS <= words <= DESCRIPTION_MAX_WORDS + WORD_TOLERANCE:
            problems.append(f"id {description.id}: {words} palavras")
        if "R$" in description.descricao:
            problems.append(f"id {description.id}: cita preço")
    return problems


def describe_batch(batch: list[Product], attempts: int = 2) -> dict[int, str]:
    for attempt in range(1, attempts + 1):
        try:
            response = get_client().messages.parse(
                model=HELPER_MODEL,
                max_tokens=DESCRIPTION_MAX_TOKENS,
                messages=[{"role": "user", "content": build_description_prompt(batch)}],
                output_format=WrittenBatch,
            )
        except ValueError as error:
            print(f"[descrições] tentativa {attempt}: JSON inválido ({error.__class__.__name__})")
            continue
        log_cost("descrições", HELPER_MODEL, response)
        problems = description_problems(batch, response.parsed_output)
        if not problems:
            return {d.id: d.descricao.strip() for d in response.parsed_output.descricoes}
        print(f"[descrições] tentativa {attempt} recusada: {'; '.join(problems)}")
    raise DescriptionFailed(f"produtos {[p.id for p in batch]}")
