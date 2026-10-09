from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.config import ALLOWED_HOSTS, API_DOCS, FRONTEND_DIR
from backend.errors import register_error_handlers
from backend.rag.search import default_policy_search, default_product_search
from backend.routes import chat, health
from backend.security import SecurityMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Carrega o modelo de embeddings e os índices ao subir: a primeira pergunta não espera por isso.
    default_product_search()
    default_policy_search()
    yield


def create_app() -> FastAPI:
    docs = {} if API_DOCS else {"docs_url": None, "redoc_url": None, "openapi_url": None}
    app = FastAPI(title="Circuito Sales Assistant", lifespan=lifespan, **docs)
    register_error_handlers(app)

    # O último adicionado roda primeiro: o Host é conferido antes de tudo.
    app.add_middleware(SecurityMiddleware)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

    app.include_router(health.router, prefix="/api")
    app.include_router(chat.router, prefix="/api")

    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    return app


app = create_app()
