from collections.abc import Generator, Iterator

from anthropic.types import Message, MessageParam, ToolUseBlock

from backend.assistant.params import assistant_params
from backend.config import ASSISTANT_MAX_ROUNDS, ASSISTANT_MODEL
from backend.prompts.assistant import ACTIVE_VERSION
from backend.llm import get_client, log_cost
from backend.sessions import Session
from backend.stream_events import event
from backend.tools.handlers import run_tool


def stream_reply(session: Session, text: str, language: str, version: str = ACTIVE_VERSION) -> Iterator[dict]:
    started_at_turn = session.turns
    new_messages: list[MessageParam] = [{"role": "user", "content": text}]

    for _ in range(ASSISTANT_MAX_ROUNDS):
        response = yield from stream_round([*session.messages, *new_messages], language, version)
        if response is None:
            yield event("error", code="stream_interrupted")
            return
        if response.stop_reason == "refusal":
            yield event("error", code="refused")
            return

        tool_uses = [block for block in response.content if block.type == "tool_use"]
        # Cortada no meio de um tool_use, a entrada da tool pode estar incompleta: não roda.
        if response.stop_reason == "max_tokens" and tool_uses:
            yield event("error", code="incomplete_reply")
            return
        if not response.content:
            yield event("error", code="empty_reply")
            return

        new_messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            if not session.commit(new_messages, started_at_turn):
                yield event("error", code="busy")
            return
        results = yield from run_tools(tool_uses)
        new_messages.append({"role": "user", "content": results})

    yield event("error", code="too_many_steps")


def stream_round(messages: list[MessageParam], language: str, version: str) -> Generator[dict, None, Message | None]:
    try:
        with get_client().messages.stream(**assistant_params(messages, language, version)) as stream:
            for chunk in stream.text_stream:
                if chunk:
                    yield event("text", text=chunk)
            response = stream.get_final_message()
    except ValueError as error:
        # Com eager_input_streaming, a API não valida a entrada da tool: um JSON quebrado estoura aqui.
        print(f"[erro] entrada de tool ilegível: {error!r}")
        return None
    log_cost("assistant", ASSISTANT_MODEL, response)
    return response


def run_tools(tool_uses: list[ToolUseBlock]) -> Generator[dict, None, list[dict]]:
    results = []
    for block in tool_uses:
        yield event("tool_call", name=block.name, input=block.input)
        outcome = run_tool(block.name, block.input)
        yield event("tool_result", name=block.name, ok=not outcome.is_error, data=outcome.data)
        results.append(outcome.as_block(block.id))
    return results
