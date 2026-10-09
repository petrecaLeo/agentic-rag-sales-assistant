from pydantic import BaseModel, ConfigDict, Field

from backend.catalog.models import Category, PaymentMethod


class ToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SearchProductsInput(ToolInput):
    consulta: str = Field(
        min_length=1, max_length=200,
        description="O que o cliente procura, em poucas palavras: nome, tipo de produto ou uso (ex.: fone para corrida).",
    )
    categoria: Category | None = Field(default=None, description="Filtra por categoria, se o cliente deixou claro.")
    # Sem teto, um 1e308 estoura ao virar centavos e derruba a resposta no meio do stream.
    preco_max: float | None = Field(
        default=None, gt=0, le=1_000_000, description="Preço máximo em reais, se o cliente deu um limite."
    )


class ProductIdInput(ToolInput):
    id: int = Field(ge=1, description="Id do produto, que vem do resultado de buscar_produtos.")


class PolicyInput(ToolInput):
    pergunta: str = Field(
        min_length=1, max_length=300, description="A dúvida do cliente sobre a loja, como frete, troca ou garantia."
    )


class ValidateCouponInput(ToolInput):
    codigo: str = Field(min_length=1, max_length=30, description="Código do cupom, como o cliente escreveu.")
    produto_id: int = Field(ge=1, description="Id do produto em que o cupom seria usado.")
    forma_pagamento: PaymentMethod | None = Field(
        default=None, description="Forma de pagamento, só se o cliente informou."
    )
