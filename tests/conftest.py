import json
import os
import tempfile
import zlib
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

# Antes de importar o back: o load_dotenv não sobrescreve variável que já existe,
# então a chave real do .env nunca entra nos testes, nem se um teste esquecer a API falsa.
os.environ["ANTHROPIC_API_KEY"] = "chave-falsa-dos-testes"

import httpx2  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402
from anthropic import Anthropic, DefaultHttpxClient  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend import llm  # noqa: E402
from backend.main import create_app  # noqa: E402
from backend.rag import embeddings  # noqa: E402
from backend.rag import search as search_module  # noqa: E402
from backend.rag.embeddings import unit_rows  # noqa: E402
from backend.rag.text import words  # noqa: E402
from backend.routes import chat as chat_route  # noqa: E402
from backend.sessions import SessionStore  # noqa: E402

ERROR_TYPES = {400: "invalid_request_error", 401: "authentication_error", 500: "api_error", 529: "overloaded_error"}


def text(value: str) -> dict:
    return {"type": "text", "text": value}


def tool_use(tool_id: str, name: str, tool_input: dict) -> dict:
    return {"type": "tool_use", "id": tool_id, "name": name, "input": tool_input}


def thinking(value: str, signature: str = "assinatura-falsa") -> dict:
    return {"type": "thinking", "thinking": value, "signature": signature}


@dataclass
class Reply:
    blocks: list[dict] = field(default_factory=lambda: [text("Olá!")])
    stop_reason: str = "end_turn"
    status: int = 200
    fail_after_events: int | None = None
    usage: tuple[int, int] = (100, 20)


class FakeAnthropicAPI:
    def __init__(self) -> None:
        self.replies: deque[Reply] = deque()
        self.requests: list[dict] = []

    def queue(self, *replies: Reply) -> None:
        self.replies.extend(replies)

    @property
    def client(self) -> Anthropic:
        transport = httpx2.MockTransport(self.handler)
        # Sem novas tentativas: um 500 roteirizado tem que chegar ao código como erro, e não ser repetido.
        return Anthropic(api_key="chave-falsa", http_client=DefaultHttpxClient(transport=transport), max_retries=0)

    def handler(self, request: httpx2.Request) -> httpx2.Response:
        body = json.loads(request.content)
        self.requests.append(body)
        problem = conversation_problem(body["messages"])
        if problem:
            return error_response(400, problem)
        if not self.replies:
            return error_response(500, "a API falsa não tem mais respostas roteirizadas")

        reply = self.replies.popleft()
        if reply.status != 200:
            return error_response(reply.status, "erro roteirizado")
        if body.get("stream"):
            return httpx2.Response(200, headers={"content-type": "text/event-stream"}, content=sse(reply, body["model"]))
        return httpx2.Response(200, json=message_json(reply, body["model"]))


def conversation_problem(messages: list[dict]) -> str | None:
    roles = [m["role"] for m in messages]
    if not roles or roles[0] != "user" or roles[-1] != "user":
        return "a conversa precisa começar e terminar com o usuário"
    if any(a == b for a, b in zip(roles, roles[1:])):
        return "os papéis precisam alternar"
    for current, following in zip(messages, messages[1:]):
        asked = sorted(block["id"] for block in blocks(current) if block["type"] == "tool_use")
        answered = sorted(block["tool_use_id"] for block in blocks(following) if block["type"] == "tool_result")
        if asked != answered:
            return "cada tool_use precisa do seu tool_result na mensagem seguinte"
    return None


def blocks(message: dict) -> list[dict]:
    return message["content"] if isinstance(message["content"], list) else []


def error_response(status: int, message: str) -> httpx2.Response:
    error = {"type": ERROR_TYPES.get(status, "api_error"), "message": message}
    return httpx2.Response(status, json={"type": "error", "error": error})


def message_json(reply: Reply, model: str) -> dict:
    return {
        "id": "msg_falsa", "type": "message", "role": "assistant", "model": model,
        "content": reply.blocks, "stop_reason": reply.stop_reason, "stop_sequence": None,
        "usage": {"input_tokens": reply.usage[0], "output_tokens": reply.usage[1]},
    }


def sse(reply: Reply, model: str) -> bytes:
    events = [("message_start", {"message": {**message_json(reply, model), "content": [], "stop_reason": None,
                                             "usage": {"input_tokens": reply.usage[0], "output_tokens": 1}}})]
    for index, block in enumerate(reply.blocks):
        events += block_events(index, block)
    events += [
        ("message_delta", {"delta": {"stop_reason": reply.stop_reason, "stop_sequence": None},
                           "usage": {"output_tokens": reply.usage[1]}}),
        ("message_stop", {}),
    ]
    if reply.fail_after_events is not None:
        events = events[: reply.fail_after_events] + [("error", {"error": {"type": "overloaded_error", "message": "caiu"}})]
    return "".join(f"event: {name}\ndata: {json.dumps({'type': name, **data})}\n\n" for name, data in events).encode()


def block_events(index: int, block: dict) -> list[tuple[str, dict]]:
    if block["type"] == "text":
        value = block["text"]
        deltas = [{"type": "text_delta", "text": value[i:i + 5]} for i in range(0, len(value), 5)]
        start = {"type": "text", "text": ""}
    elif block["type"] == "tool_use":
        deltas = [{"type": "input_json_delta", "partial_json": json.dumps(block["input"])}]
        start = {**block, "input": {}}
    elif block["type"] == "thinking":
        deltas = [{"type": "thinking_delta", "thinking": block["thinking"]},
                  {"type": "signature_delta", "signature": block["signature"]}]
        start = {"type": "thinking", "thinking": "", "signature": ""}
    else:
        raise ValueError(f"bloco sem roteiro de stream: {block['type']}")
    return (
        [("content_block_start", {"index": index, "content_block": start})]
        + [("content_block_delta", {"index": index, "delta": delta}) for delta in deltas]
        + [("content_block_stop", {"index": index})]
    )


@pytest.fixture
def fake_api(monkeypatch) -> FakeAnthropicAPI:
    api = FakeAnthropicAPI()
    monkeypatch.setattr(llm, "_client", api.client)
    return api


@pytest.fixture
def session_store(monkeypatch) -> SessionStore:
    store = SessionStore()
    monkeypatch.setattr(chat_route, "sessions", store)
    return store


@pytest.fixture
def client(fake_api, session_store) -> TestClient:
    # App novo a cada teste: o contador do rate limit não passa de um teste para o outro.
    return TestClient(create_app(), base_url="http://localhost")


def send(client: TestClient, message: str, **extra) -> tuple[int, list[dict]]:
    response = client.post("/api/chat", json={"message": message, **extra})
    if response.headers["content-type"].startswith("application/x-ndjson"):
        return response.status_code, [json.loads(line) for line in response.text.splitlines() if line]
    return response.status_code, [response.json()]


class HashEmbedder:
    name = "hash-dos-testes"

    def __init__(self, dimensions: int = 64) -> None:
        self.dimensions = dimensions
        self.calls = 0

    def embed(self, texts: list[str]) -> np.ndarray:
        self.calls += 1
        vectors = np.zeros((len(texts), self.dimensions), dtype=np.float32)
        for row, text in enumerate(texts):
            for word in words(text):
                vectors[row, zlib.crc32(word.encode()) % self.dimensions] += 1
        return unit_rows(vectors)


def forbidden_model(*args, **kwargs):
    raise RuntimeError("os testes não podem carregar o modelo de embeddings")


# No import do conftest, antes de qualquer teste ser importado: alguns montam a busca padrão no nível do módulo,
# e uma fixture chegaria tarde. Mesma ideia da chave falsa: nenhum teste carrega o modelo de 220 MB.
embeddings.FastEmbedder = forbidden_model
search_module.default_embedder = HashEmbedder
search_module.CACHE_DIR = Path(tempfile.mkdtemp(prefix="sales-assistant-tests-"))
