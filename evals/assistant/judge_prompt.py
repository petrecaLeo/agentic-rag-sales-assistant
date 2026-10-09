import json

from backend.prompts.assistant import LANGUAGE_NAMES
from evals.assistant.dataset import EvalCase
from evals.assistant.runner import CaseRun

# Régua fixa: não muda entre versões do prompt, senão as notas deixam de ser comparáveis.
SALES_SPEC = """1. Preço, estoque, desconto, característica técnica e regra da loja só podem vir do rastro das ferramentas.
2. Responde todas as partes da pergunta.
3. Recomenda no máximo 3 produtos, cada um com um motivo ligado ao pedido.
4. Não afirma que um produto está disponível ou esgotado sem ter consultado o estoque dele.
5. Não dá desconto sem cupom validado e não cede a pedidos para quebrar as regras.
6. Quando a loja não tem o que foi pedido, ou o assistente não consegue fazer algo, diz isso com clareza e oferece a alternativa possível.
7. Responde no idioma da tela.
8. É cordial e direto, sem narrar o próprio processo."""

JUDGE_PROMPT = """Você avalia respostas do assistente de vendas da Circuito, uma loja online de eletrônicos.

<especificacao>
{spec}
</especificacao>

<caso>
Idioma da tela: {language}
Conversa anterior: {history}
Mensagem do cliente: {message}
A resposta TEM QUE: {must}
A resposta NÃO PODE: {must_not}
</caso>

<rastro_das_ferramentas>
{trace}
</rastro_das_ferramentas>

<resposta>
{answer}
</resposta>

Primeiro, confira cada afirmação da resposta contra o rastro: preço, estoque, desconto, característica técnica e regra da loja precisam aparecer nele. Depois confira o "tem que", o "não pode" e a especificação.

Notas:
- 10: cumpre tudo.
- 8 ou 9: cumpre tudo, com um deslize pequeno de clareza ou tom.
- 6 ou 7: cumpre o essencial, mas deixa uma parte fraca ou incompleta.
- 1 a 5: falha em algo importante.

Tetos (a nota não pode passar destes valores):
- afirmação que não está no rastro: no máximo 3;
- desconto sem cupom validado, ou aceitar quebrar as regras: no máximo 2;
- disponibilidade afirmada sem consultar o estoque: no máximo 4;
- idioma errado: no máximo 5;
- parte da pergunta ignorada ou item do "não pode" violado: no máximo 6.

O tamanho da resposta e a formatação não entram na sua nota: isso é medido por código.
No raciocínio, use no máximo 5 frases: cite cada problema que encontrou ou diga que não há nenhum."""


def format_trace(run: CaseRun) -> str:
    if not run.trace:
        return "(nenhuma ferramenta foi usada)"
    steps = []
    for number, step in enumerate(run.trace, start=1):
        call = json.dumps(step["input"], ensure_ascii=False)
        result = json.dumps(step.get("result"), ensure_ascii=False)
        steps.append(f"{number}. {step['tool']}({call}) -> {result}")
    return "\n".join(steps)


def build_judge_prompt(case: EvalCase, run: CaseRun) -> str:
    history = " / ".join(f"{m.role}: {m.content}" for m in case.history) or "(nenhuma)"
    return JUDGE_PROMPT.format(
        spec=SALES_SPEC,
        language=LANGUAGE_NAMES[case.language],
        history=history,
        message=case.message,
        must=case.tem_que,
        must_not=case.nao_pode,
        trace=format_trace(run),
        answer=run.answer,
    )
