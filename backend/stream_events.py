import json
import traceback
from collections.abc import Iterator

import anthropic


def event(kind: str, **data) -> dict:
    return {"type": kind, **data}


def as_ndjson(events: Iterator[dict]) -> Iterator[str]:
    try:
        for item in events:
            yield json.dumps(item, ensure_ascii=False) + "\n"
            if item["type"] == "error":
                return
    except anthropic.APIError as error:
        # O status 200 já foi enviado: o erro só pode ir como evento.
        print(f"[erro] stream interrompido: {error!r}")
        yield json.dumps(event("error", code="stream_interrupted")) + "\n"
        return
    except Exception:
        # Um bug no meio do stream: o detalhe fica no log do servidor, e a tela recebe só um código.
        traceback.print_exc()
        yield json.dumps(event("error", code="stream_interrupted")) + "\n"
        return
    yield json.dumps(event("done")) + "\n"
