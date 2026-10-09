import { readPreference, savePreference } from "./storage.js";
import { translations } from "./translations.js";

const HTML_LANG = { pt: "pt-BR", en: "en" };

let language = detectLanguage();

function detectLanguage() {
  const saved = readPreference("language");
  if (saved && saved in translations) return saved;
  return navigator.language.toLowerCase().startsWith("pt") ? "pt" : "en";
}

export function getLanguage() {
  return language;
}

export function t(key) {
  return translations[language][key] ?? key;
}

export function applyTranslations() {
  document.documentElement.lang = HTML_LANG[language];
  document.title = t("app.title");

  for (const element of document.querySelectorAll("[data-i18n]")) {
    element.textContent = t(element.dataset.i18n);
  }
  for (const element of document.querySelectorAll("[data-i18n-placeholder]")) {
    element.placeholder = t(element.dataset.i18nPlaceholder);
  }
  for (const element of document.querySelectorAll("[data-i18n-label]")) {
    element.setAttribute("aria-label", t(element.dataset.i18nLabel));
  }
  for (const button of document.querySelectorAll("[data-language]")) {
    button.setAttribute("aria-pressed", String(button.dataset.language === language));
  }
}

export function setupLanguageSwitcher() {
  for (const button of document.querySelectorAll("[data-language]")) {
    button.addEventListener("click", () => {
      language = button.dataset.language;
      savePreference("language", language);
      applyTranslations();
    });
  }
}
