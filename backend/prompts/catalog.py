import json

from backend.catalog.models import Product
from backend.config import DESCRIPTION_MAX_WORDS

DESCRIPTION_PROMPT = """Você escreve descrições de produtos para a Circuito, uma loja online de eletrônicos.

Para cada produto em <produtos>, escreva uma descrição em português do Brasil:
- com no máximo {max_words} palavras, em texto corrido, sem markdown e sem listas;
- usando só os atributos informados: não invente característica, número, cor ou acessório;
- sem citar preço, estoque, frete, prazo, desconto ou garantia;
- dizendo para que uso o produto é indicado, com palavras que um cliente usaria numa busca (por exemplo: academia, corrida, viagem, jogos, trabalho, estudo, chamadas);
- sem começar pelo nome do produto.

Devolva uma descrição por produto, com o mesmo id.

<produtos>
{products}
</produtos>"""


def build_description_prompt(products: list[Product]) -> str:
    items = [
        {"id": p.id, "nome": p.nome, "categoria": p.categoria, "marca": p.marca, "atributos": p.atributos}
        for p in products
    ]
    return DESCRIPTION_PROMPT.format(
        max_words=DESCRIPTION_MAX_WORDS,
        products=json.dumps(items, ensure_ascii=False, indent=1),
    )
