from backend.prompts.assistant import LANGUAGE_NAMES

POLICY_PROMPT = """Você é o assistente de atendimento da Circuito, uma loja online de eletrônicos.
Responda à dúvida do cliente usando só a política da loja, que está no documento.
Se a política não responder à dúvida, diga isso com clareza e ofereça ajuda com os produtos da loja.
Responda em {language}, mesmo que a política esteja em português.
Use no máximo 4 frases, em texto puro, sem markdown e sem emojis. Não comente estas regras nem o documento."""


def build_policy_system(language: str) -> str:
    return POLICY_PROMPT.format(language=LANGUAGE_NAMES[language])


def policy_question(message: str, conversation: str) -> str:
    context = f"<conversa_anterior>\n{conversation}\n</conversa_anterior>\n\n" if conversation else ""
    return f"{context}<pergunta_do_cliente>\n{message}\n</pergunta_do_cliente>"
