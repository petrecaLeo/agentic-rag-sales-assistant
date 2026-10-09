import { t } from "./i18n.js";

const MAX_INPUT_CHARS = 60;

function clip(value) {
  return String(value ?? "").slice(0, MAX_INPUT_CHARS);
}

function fill(template, values) {
  return template.replace(/\{(\w+)\}/g, (_, key) => clip(values[key]));
}

export function toolLabel(name, input = {}) {
  const template = t(`tools.${name}`);
  if (template === `tools.${name}`) return t("tools.unknown");

  let label = fill(template, input);
  if (name === "buscar_produtos" && input.categoria) {
    label += fill(t("tools.filter.category"), { categoria: t(`categories.${input.categoria}`) });
  }
  if (name === "buscar_produtos" && input.preco_max) {
    label += fill(t("tools.filter.maxPrice"), { preco: Number(input.preco_max).toLocaleString("pt-BR") });
  }
  return label;
}
