from pathlib import Path

LANGUAGE_NAMES = {
    "pt": "português do Brasil",
    "en": "inglês",
}

# Cada versão do prompt do assistente é um arquivo de texto: assistant_versions/v1.txt, v2.txt…
VERSIONS_DIR = Path(__file__).parent / "assistant_versions"
ASSISTANT_PROMPTS = {path.stem: path.read_text(encoding="utf-8").strip() for path in VERSIONS_DIR.glob("v*.txt")}

ACTIVE_VERSION = "v2"


def build_system(language: str, version: str = ACTIVE_VERSION) -> str:
    return ASSISTANT_PROMPTS[version].format(language=LANGUAGE_NAMES[language])
