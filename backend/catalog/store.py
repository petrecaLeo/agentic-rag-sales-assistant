import json
from functools import cache
from pathlib import Path

from backend.catalog.models import Product
from backend.config import CATALOG_FILE


class Catalog:
    def __init__(self, products: list[Product]) -> None:
        self.products = products
        self._by_id = {product.id: product for product in products}

    @classmethod
    def from_file(cls, path: Path = CATALOG_FILE) -> "Catalog":
        items = json.loads(path.read_text(encoding="utf-8"))
        return cls([Product.model_validate(item) for item in items])

    def get(self, product_id: int) -> Product | None:
        return self._by_id.get(product_id)

    def __len__(self) -> int:
        return len(self.products)


@cache
def default_catalog() -> Catalog:
    return Catalog.from_file()
