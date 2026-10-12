import json

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

mcp = MCPServer("Loja falsa", log_level="ERROR")


@mcp.tool(name="consultar_estoque")
def stock(id: int) -> dict:
    if id != 58:
        raise ToolError(json.dumps({"erro": f"Não existe produto com id {id}."}, ensure_ascii=False))
    return {"id": 58, "estoque": 30, "disponivel": True}


if __name__ == "__main__":
    mcp.run()
