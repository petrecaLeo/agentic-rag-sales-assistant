import { t } from "./i18n.js";

const SUGGESTIONS = [
  { key: "suggestion.gym", icon: "headphones" },
  { key: "suggestion.coupon", icon: "ticket" },
  { key: "suggestion.return", icon: "return" },
];

function translated(tagName, key) {
  const element = document.createElement(tagName);
  element.dataset.i18n = key;
  element.textContent = t(key);
  return element;
}

function suggestionButton({ key, icon }, onPick) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "suggestion";
  const iconElement = document.createElement("span");
  iconElement.className = `suggestion-icon ${icon}`;
  button.append(iconElement, translated("span", key));
  button.addEventListener("click", () => onPick(t(key)));
  return button;
}

export function showOpener(onPick) {
  const opener = document.createElement("section");
  opener.className = "opener";

  const suggestions = document.createElement("div");
  suggestions.className = "suggestions";
  suggestions.setAttribute("role", "group");
  suggestions.dataset.i18nLabel = "opener.suggestions";
  suggestions.setAttribute("aria-label", t("opener.suggestions"));
  suggestions.append(...SUGGESTIONS.map((suggestion) => suggestionButton(suggestion, onPick)));

  opener.append(translated("h2", "opener.title"), translated("p", "opener.text"), suggestions);
  document.getElementById("messages").append(opener);
}
