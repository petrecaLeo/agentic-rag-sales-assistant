import asyncio
import json
import sys
import threading
from concurrent.futures import Future

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from backend.config import ROOT_DIR
from backend.tools.handlers import ToolOutcome

START_TIMEOUT_SECONDS = 60
CALL_TIMEOUT_SECONDS = 30


def error_data(text: str) -> dict:
    # O SDK escreve "Error executing tool <nome>: <mensagem>"; a mensagem do servidor da loja é o JSON do erro.
    _, _, detail = text.partition(": ")
    try:
        data = json.loads(detail)
    except ValueError:
        return {"erro": text}
    return data if isinstance(data, dict) else {"erro": text}


class McpTools:
    # O loop do agente é síncrono e o cliente MCP é assíncrono: a sessão fica aberta numa thread com o próprio event loop.
    def __init__(self, command: str = sys.executable, args: list[str] | None = None) -> None:
        self._params = StdioServerParameters(command=command, args=args or ["mcp_server.py"], cwd=ROOT_DIR)
        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self._loop.run_forever, daemon=True).start()
        self._stop = asyncio.Event()
        ready: Future[ClientSession] = Future()
        asyncio.run_coroutine_threadsafe(self._serve(ready), self._loop)
        self._session = ready.result(timeout=START_TIMEOUT_SECONDS)

    async def _serve(self, ready: Future) -> None:
        try:
            async with stdio_client(self._params) as (receive, send), ClientSession(receive, send) as session:
                await session.initialize()
                ready.set_result(session)
                await self._stop.wait()
        except Exception as error:
            if not ready.done():
                ready.set_exception(error)
            raise

    def call(self, name: str, arguments: object) -> ToolOutcome:
        call = self._session.call_tool(name, arguments if isinstance(arguments, dict) else {})
        result = asyncio.run_coroutine_threadsafe(call, self._loop).result(timeout=CALL_TIMEOUT_SECONDS)
        text = "".join(block.text for block in result.content if block.type == "text")
        if result.is_error:
            return ToolOutcome(error_data(text), is_error=True)
        return ToolOutcome(json.loads(text))


_lock = threading.Lock()
_tools: McpTools | None = None


def mcp_tools() -> McpTools:
    global _tools
    # As rotas síncronas rodam em várias threads: sem o lock, duas primeiras perguntas abririam dois servidores.
    with _lock:
        if _tools is None:
            _tools = McpTools()
        return _tools
