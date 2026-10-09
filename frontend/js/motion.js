const DURATION = 240;
const EASING = "cubic-bezier(0.2, 0.7, 0.2, 1)";
// Elementos grandes saem mais devagar e com começo suave: a mesma curva rápida viraria um tranco.
const LEAVE_DURATION = 420;
const LEAVE_EASING = "cubic-bezier(0.4, 0, 0.2, 1)";

function reducedMotion() {
  return matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function run(element, keyframes, duration = DURATION, easing = EASING) {
  if (reducedMotion()) return Promise.resolve();
  const overflow = element.style.overflow;
  element.style.overflow = "hidden";
  return element
    .animate(keyframes, { duration, easing })
    .finished.catch(() => {})
    .finally(() => {
      element.style.overflow = overflow;
    });
}

// Anima da altura antiga até a atual: quem está abaixo desce ou sobe aos poucos, sem pulo.
export function growFrom(element, fromHeight) {
  const height = element.offsetHeight;
  if (height === fromHeight) return Promise.resolve();
  return run(element, [{ height: `${fromHeight}px` }, { height: `${height}px` }]);
}

export function reveal(element) {
  const height = element.offsetHeight;
  return run(element, [{ height: "0px", opacity: 0 }, { height: `${height}px`, opacity: 1 }]);
}

// O padding também vai a zero: senão a altura trava no padding e o resto some de uma vez no fim.
// O `gap` desconta o espaço que o flex põe entre os itens, pelo mesmo motivo.
// A opacidade zera na metade, para o texto sumir antes de a caixa encolhida cortá-lo.
export async function collapse(element, gap = 0) {
  const { paddingTop, paddingBottom } = getComputedStyle(element);
  const height = element.offsetHeight;
  await run(
    element,
    [
      { height: `${height}px`, paddingTop, paddingBottom, opacity: 1, marginBottom: "0px" },
      { opacity: 0, offset: 0.5 },
      { height: "0px", paddingTop: "0px", paddingBottom: "0px", opacity: 0, marginBottom: `${-gap}px` },
    ],
    LEAVE_DURATION,
    LEAVE_EASING,
  );
  element.remove();
}
