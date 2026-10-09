import { renderCards } from "./cards.js";
import { t } from "./i18n.js";
import { collapse, growFrom, reveal } from "./motion.js";

const list = document.getElementById("messages");

function isNearBottom() {
  return list.scrollHeight - list.scrollTop - list.clientHeight < 80;
}

function scrollToBottom() {
  list.scrollTop = list.scrollHeight;
}

// Quem subiu para reler a conversa não é puxado de volta para o fim.
// Quem está no fim acompanha a animação quadro a quadro, em vez de um pulo quando ela acaba.
function keepingScroll(update) {
  const stick = isNearBottom();
  const animation = update() ?? Promise.resolve();
  if (!stick) return;
  let running = true;
  animation.finally(() => {
    running = false;
    scrollToBottom();
  });
  const follow = () => {
    scrollToBottom();
    if (running) requestAnimationFrame(follow);
  };
  follow();
}

function dots() {
  return Array.from({ length: 3 }, () => document.createElement("span"));
}

export function addMessage(role, text) {
  const message = document.createElement("div");
  message.className = `message ${role}`;
  message.textContent = text;
  list.append(message);
  scrollToBottom();
  return message;
}

export function clearMessages() {
  list.replaceChildren();
  list.removeAttribute("aria-busy");
}

export function dismissOpener() {
  const opener = list.querySelector(".opener");
  if (opener) collapse(opener, parseFloat(getComputedStyle(list).rowGap) || 0);
}

export function addPendingReply() {
  const message = document.createElement("div");
  message.className = "message assistant pending";
  message.setAttribute("aria-label", t("chat.typing"));
  const steps = document.createElement("ul");
  steps.className = "steps";
  const body = document.createElement("div");
  body.className = "text";
  body.append(...dots());
  message.append(steps, body);
  list.append(message);
  list.setAttribute("aria-busy", "true");
  scrollToBottom();

  const addStep = (className, text) => {
    const item = document.createElement("li");
    item.className = className;
    item.textContent = text;
    keepingScroll(() => {
      steps.append(item);
      return reveal(item);
    });
    return item;
  };

  // Terminada a resposta, os passos viram uma linha só, que abre com um clique.
  const collapseSteps = () => {
    const count = steps.querySelectorAll(".step:not(.note)").length;
    if (!count) return;
    const details = document.createElement("details");
    details.className = "steps-summary";
    const summary = document.createElement("summary");
    summary.textContent = count === 1 ? t("steps.one") : t("steps.many").replace("{n}", count);
    const before = steps.offsetHeight;
    steps.replaceWith(details);
    details.append(summary, steps);
    keepingScroll(() => growFrom(details, before));
  };

  const finish = (role, text) => {
    message.className = `message ${role}`;
    message.removeAttribute("aria-label");
    body.textContent = text;
  };

  return {
    write: (text) => {
      if (text) return keepingScroll(() => finish("assistant", text));
      // Texto vazio: a narração virou passo, e os pontinhos voltam enquanto a próxima volta não chega.
      keepingScroll(() => {
        const before = body.offsetHeight;
        message.className = "message assistant pending";
        body.replaceChildren(...dots());
        return growFrom(body, before);
      });
    },
    note: (text) => addStep("step note", text),
    step: (label) => {
      const item = addStep("step running", label);
      return (ok) => {
        item.className = `step ${ok ? "done" : "failed"}`;
      };
    },
    cards: (products) => {
      if (!products.length) return;
      const grid = renderCards(products);
      keepingScroll(() => {
        message.append(grid);
        return reveal(grid);
      });
    },
    done: () => {
      collapseSteps();
      list.removeAttribute("aria-busy");
    },
    fail: (text) => {
      keepingScroll(() => finish("error", text));
      list.removeAttribute("aria-busy");
    },
  };
}
