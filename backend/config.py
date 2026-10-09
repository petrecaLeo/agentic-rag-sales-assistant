import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
DATA_DIR = ROOT_DIR / "data"
CATALOG_FILE = DATA_DIR / "catalog.json"
COUPONS_FILE = DATA_DIR / "coupons.json"
POLICY_FILE = DATA_DIR / "policy.txt"
CACHE_DIR = DATA_DIR / "cache"

EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

load_dotenv(ROOT_DIR / ".env")

ASSISTANT_MODEL = "claude-sonnet-5-5"
HELPER_MODEL = "claude-haiku-4-5"

# US$ por milhão de tokens: (entrada, saída)
PRICES = {
    ASSISTANT_MODEL: (2, 10),
    HELPER_MODEL: (1, 5),
}

ASSISTANT_MAX_TOKENS = 500
ASSISTANT_MAX_ROUNDS = 6
SEARCH_LIMIT = 5
POLICY_LIMIT = 3

SEARCH_METHOD = "hibrido"
RRF_K = 60
RRF_DEPTH = 50
# Medido na eval: toda consulta válida tem o 1º produto acima de 0,50; "geladeira" fica em 0,31.
PRODUCT_MIN_SIMILARITY = 0.40

DESCRIPTION_BATCH_SIZE = 3
DESCRIPTION_MAX_TOKENS = 500
DESCRIPTION_MAX_WORDS = 60

JUDGE_MAX_TOKENS = 600

MAX_USER_MESSAGE_CHARS = 1000

# O Sonnet 5.5 exige histórico só com acréscimos, então o custo é limitado por rodadas, e não por um corte.
SESSION_TTL_SECONDS = 30 * 60
MAX_SESSIONS = 200
MAX_TURNS_PER_SESSION = 20

ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host.strip()]
# A maior mensagem válida (1.000 emojis escapados como \uXXXX) tem uns 12 KB.
MAX_BODY_BYTES = 16_384
RATE_LIMIT_PER_MINUTE = 20
API_DOCS = os.getenv("API_DOCS") == "1"
