from datetime import date
from typing import Literal

from pydantic import BaseModel

Category = Literal["celulares", "notebooks", "fones", "acessorios"]
PaymentMethod = Literal["pix", "cartao", "boleto"]

CATEGORY_NAMES: dict[Category, str] = {
    "celulares": "celulares",
    "notebooks": "notebooks",
    "fones": "fones de ouvido",
    "acessorios": "acessórios",
}


class Product(BaseModel):
    id: int
    nome: str
    categoria: Category
    marca: str
    preco: int
    estoque: int
    atributos: dict[str, str]
    descricao: str = ""


class Coupon(BaseModel):
    codigo: str
    tipo: Literal["percentual", "fixo"]
    valor: int
    categorias: list[Category] | None = None
    minimo: int = 0
    validade: date | None = None
    pagamento: PaymentMethod | None = None
