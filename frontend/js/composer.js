export function setupComposer(onSend) {
  const form = document.getElementById("composer");
  const input = document.getElementById("composer-input");
  const sendButton = form.querySelector("button[type=submit]");

  const autoGrow = () => {
    input.style.height = "auto";
    const borders = input.offsetHeight - input.clientHeight;
    input.style.height = `${input.scrollHeight + borders}px`;
  };

  input.addEventListener("input", autoGrow);

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text || sendButton.disabled) return;

    input.value = "";
    autoGrow();
    sendButton.disabled = true;
    try {
      await onSend(text);
    } finally {
      sendButton.disabled = false;
      input.focus();
    }
  });

  // Em tela de toque, focar sozinho abriria o teclado.
  if (matchMedia("(pointer: fine)").matches) input.focus();

  return {
    send(text) {
      input.value = text;
      form.requestSubmit();
    },
  };
}
