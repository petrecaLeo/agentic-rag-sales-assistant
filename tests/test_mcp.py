import sys

import pytest
from mcp.server.mcpserver.tools.base import Tool

from backend.assistant import loop
from backend.assistant.profiles import PROFILES
from backend.mcp_server import tool_function
from backend.tools.definitions import TOOL_INPUTS, TOOLS, without_titles
from backend.sessions import Session
from backend.tools.handlers import ToolOutcome
from backend.tools.mcp_client import McpTools, error_data
from tests.conftest import Reply, text, tool_use


@pytest.mark.parametrize("tool", TOOLS, ids=lambda tool: tool["name"])
def test_the_mcp_server_publishes_the_same_schema_the_app_sends(tool):
    published = Tool.from_function(tool_function(tool["name"], TOOL_INPUTS[tool["name"]])).parameters
    app = {key: value for key, value in tool["input_schema"].items() if key != "additionalProperties"}

    assert without_titles(published) == app


def test_error_text_from_the_sdk_becomes_the_store_error():
    assert error_data('Error executing tool x: {"erro": "Não existe."}') == {"erro": "Não existe."}
    assert error_data("Error executing tool x: falhou") == {"erro": "Error executing tool x: falhou"}


def test_the_client_calls_a_real_mcp_server_over_stdio():
    tools = McpTools(sys.executable, ["-m", "tests.fakes.mcp_store"])

    assert tools.call("consultar_estoque", {"id": 58}) == ToolOutcome({"id": 58, "estoque": 30, "disponivel": True})
    missing = tools.call("consultar_estoque", {"id": 7})
    assert missing.is_error and missing.data == {"erro": "Não existe produto com id 7."}


def test_the_mcp_profile_runs_tools_through_the_mcp_client(fake_api, monkeypatch):
    calls = []

    class FakeMcp:
        def call(self, name, arguments):
            calls.append((name, arguments))
            return ToolOutcome({"id": 58, "estoque": 30, "disponivel": True})

    monkeypatch.setattr(loop, "mcp_tools", FakeMcp)
    fake_api.queue(Reply([tool_use("t1", "consultar_estoque", {"id": 58})], stop_reason="tool_use"),
                   Reply([text("Tem 30 unidades.")]))

    events = list(loop.stream_reply(Session(id="s", last_seen=0), "tem estoque?", "pt", PROFILES["mcp"]))

    assert calls == [("consultar_estoque", {"id": 58})]
    assert [e for e in events if e["type"] == "tool_result"][0]["data"]["estoque"] == 30
