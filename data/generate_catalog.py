import json
import sys
from itertools import batched
from pathlib import Path

from backend.catalog.models import Product
from backend.config import CATALOG_FILE, DESCRIPTION_BATCH_SIZE
from backend.llm import spending
from data.generator import draw_products
from data.generator.describe import DescriptionFailed, describe_batch


def load_or_draw(path: Path) -> list[Product]:
    if path.exists():
        return [Product.model_validate(item) for item in json.loads(path.read_text(encoding="utf-8"))]
    return draw_products()


def save(products: list[Product], path: Path) -> None:
    data = [product.model_dump() for product in products]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(path: Path = CATALOG_FILE) -> int:
    # Nunca reescreve uma descrição pronta: rodar de novo só completa as que faltam.
    products = load_or_draw(path)
    missing = [p for p in products if not p.descricao]
    if not missing:
        print(f"{path.name} já está completo ({len(products)} produtos).")
        return 0

    failed = []
    for batch in batched(missing, DESCRIPTION_BATCH_SIZE):
        try:
            descriptions = describe_batch(list(batch))
        except DescriptionFailed as error:
            failed.append(str(error))
            continue
        for product in batch:
            product.descricao = descriptions[product.id]
        save(products, path)

    print(f"{len(products) - sum(not p.descricao for p in products)}/{len(products)} produtos com descrição")
    print(f"custo total: ${spending.total:.6f}")
    if failed:
        print(f"falharam: {failed}. Rode de novo para completar.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
