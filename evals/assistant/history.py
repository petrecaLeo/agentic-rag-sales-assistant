import json

from evals.assistant.report import RESULTS_DIR


def main() -> None:
    print("| arquivo | versão | código | juiz | final | preços sem fonte | custo |")
    print("|---|---|---|---|---|---|---|")
    for path in sorted(RESULTS_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        s = data["summary"]
        print(f"| {path.stem} | {data['version']} | {s['code']} | {s['judge']} | {s['final']} | "
              f"{s['ungrounded_prices']} | ${s['cost']:.4f} |")


if __name__ == "__main__":
    main()
