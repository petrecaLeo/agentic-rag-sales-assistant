import json

from evals.assistant.report import RESULTS_DIR


def cell(summary: dict, key: str, unit: str = "") -> str:
    value = summary.get(key)
    return "-" if value is None else f"{value}{unit}"


def main() -> None:
    print("| arquivo | perfil | final | custo/pergunta | tempo | 1ª palavra | chamadas | custo total |")
    print("|---|---|---|---|---|---|---|---|")
    for path in sorted(RESULTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime):
        data = json.loads(path.read_text(encoding="utf-8"))
        s = data["summary"]
        # Os arquivos da semana 3 guardavam a versão do prompt, e não o perfil, e não mediam tempo.
        name = data.get("profile") or f"prompt {data['version']}"
        cost_per_question = "-" if "cost_per_question" not in s else f"${s['cost_per_question']:.4f}"
        print(f"| {path.stem} | {name} | {s['final']} | {cost_per_question} | {cell(s, 'seconds', ' s')} | "
              f"{cell(s, 'first_word_seconds', ' s')} | {cell(s, 'calls_per_question')} | ${s['cost']:.4f} |")


if __name__ == "__main__":
    main()
