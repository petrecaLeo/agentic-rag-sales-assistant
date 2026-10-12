import inspect
import json
from collections.abc import Callable
from typing import Annotated

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel

from backend.assistant.policy_path import policy_text
from backend.prompts.policy import build_policy_system
from backend.rag.search import default_policy_search, default_product_search
from backend.tools.definitions import DESCRIPTIONS, TOOL_INPUTS
from backend.tools.handlers import run_tool

mcp = MCPServer("Circuito", instructions="Ferramentas da Circuito, uma loja online de eletrônicos.", log_level="ERROR")


def tool_function(name: str, model: type[BaseModel]) -> Callable[..., dict]:
    def call(**arguments) -> dict:
        outcome = run_tool(name, arguments)
        if outcome.is_error:
            raise ToolError(json.dumps(outcome.data, ensure_ascii=False))
        return outcome.data

    # A assinatura sai do mesmo modelo pydantic que o app usa: o schema que o MCP publica e o que o Claude vê no app
    # têm os mesmos campos, descrições e limites.
    call.__signature__ = inspect.Signature(
        [
            inspect.Parameter(
                field_name,
                inspect.Parameter.KEYWORD_ONLY,
                annotation=Annotated[field.annotation, field],
                default=inspect.Parameter.empty if field.is_required() else field.default,
            )
            for field_name, field in model.model_fields.items()
        ],
        return_annotation=dict,
    )
    call.__name__ = name
    return call


for tool_name, input_model in TOOL_INPUTS.items():
    mcp.add_tool(tool_function(tool_name, input_model), name=tool_name, description=DESCRIPTIONS[tool_name])


@mcp.resource(
    "circuito://politica",
    name="politica",
    description="Política da Circuito: frete, entrega, pagamento, cupons, trocas, devoluções, garantia e reembolso.",
    mime_type="text/plain",
)
def policy_resource() -> str:
    return policy_text()


@mcp.prompt(name="atendimento", description="Pedido pronto para responder a uma dúvida de cliente com a política da loja.")
def service_prompt(pergunta: str, idioma: str = "pt") -> str:
    return f"{build_policy_system(idioma)}\n\n<politica>\n{policy_text()}\n</politica>\n\nPergunta do cliente: {pergunta}"


def main() -> None:
    # Carrega o modelo de embeddings antes do primeiro pedido, como o app faz no lifespan.
    default_product_search()
    default_policy_search()
    mcp.run()


if __name__ == "__main__":
    main()
