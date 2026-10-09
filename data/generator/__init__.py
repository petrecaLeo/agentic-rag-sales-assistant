import random

from backend.catalog.models import Product
from data.generator.accessories import draw_accessories
from data.generator.common import SEED
from data.generator.headphones import draw_headphones
from data.generator.notebooks import draw_notebooks
from data.generator.phones import draw_phones


def draw_products(seed: int = SEED) -> list[Product]:
    rng = random.Random(seed)
    drafts = [*draw_phones(rng), *draw_notebooks(rng), *draw_headphones(rng), *draw_accessories(rng)]
    return [Product(id=index, **draft) for index, draft in enumerate(drafts, start=1)]
