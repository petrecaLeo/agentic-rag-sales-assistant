import { t } from "./i18n.js";
import { readNdjson } from "./ndjson.js";

function errorMessage(code) {
  const message = t(`errors.${code}`);
  return message === `errors.${code}` ? t("errors.unknown") : message;
}

async function post(path, body) {
  let response;
  try {
    response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new Error(errorMessage("server_down"));
  }

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(errorMessage(data.code ?? "unknown"));
  }
  return response;
}

export async function streamChat({ message, sessionId, language }, { onSession, onText, onNote, onToolCall, onToolResult }) {
  const body = { message, language };
  if (sessionId) body.session_id = sessionId;
  const response = await post("/api/chat", body);

  // Texto escrito antes de uma tool é narração do caminho ("vou buscar…"): vira um passo, e a resposta é só o que vem depois da última tool.
  let text = "";
  const runningTools = [];
  // Sem um evento "done" no fim, a conexão caiu no meio.
  let outcome = "stream_interrupted";

  try {
    for await (const event of readNdjson(response.body)) {
      if (event.type === "session") {
        onSession(event.id);
      } else if (event.type === "text") {
        text += event.text;
        onText(text);
      } else if (event.type === "tool_call") {
        if (text.trim()) onNote(text.trim());
        text = "";
        onText(text);
        runningTools.push(onToolCall(event.name, event.input));
      } else if (event.type === "tool_result") {
        runningTools.shift()?.(event.ok);
        if (event.ok) onToolResult(event.name, event.data);
      } else {
        outcome = event.type === "done" ? "done" : event.code;
      }
    }
  } catch {
    outcome = "stream_interrupted";
  }

  if (outcome !== "done") throw new Error(errorMessage(outcome));
  if (!text.trim()) throw new Error(errorMessage("empty_reply"));
  return text;
}
