import { streamChat } from "./api.js";
import { createCardCollector } from "./cards.js";
import { addMessage, addPendingReply, clearMessages, dismissOpener } from "./chat.js";
import { setupComposer } from "./composer.js";
import { applyTranslations, getLanguage, setupLanguageSwitcher } from "./i18n.js";
import { showOpener } from "./opener.js";
import { toolLabel } from "./tools.js";

applyTranslations();
setupLanguageSwitcher();

let sessionId = null;
let conversation = 0;

const composer = setupComposer(async (text) => {
  // Uma resposta que chegar depois de "Nova conversa" não pode trazer de volta a sessão antiga.
  const current = conversation;
  dismissOpener();
  addMessage("user", text);
  const reply = addPendingReply();
  const cards = createCardCollector();

  try {
    await streamChat(
      { message: text, sessionId, language: getLanguage() },
      {
        onSession: (id) => {
          if (current === conversation) sessionId = id;
        },
        onText: reply.write,
        onNote: reply.note,
        onToolCall: (name, input) => reply.step(toolLabel(name, input)),
        onToolResult: cards.add,
      },
    );
    reply.cards(cards.cards());
    reply.done();
  } catch (error) {
    reply.fail(error.message);
  }
});

function startConversation() {
  conversation += 1;
  sessionId = null;
  clearMessages();
  showOpener(composer.send);
}

document.getElementById("new-chat").addEventListener("click", startConversation);
startConversation();
