"""Runtime settings, read once from the environment."""

import os


def _normalize_database_url(url: str) -> str:
    # psycopg ne comprend pas le préfixe SQLAlchemy postgresql+psycopg://
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


def _int(name: str, default: int) -> int:
    return int(os.environ.get(name) or default)


def _float(name: str, default: float) -> float:
    return float(os.environ.get(name) or default)


DATABASE_URL = _normalize_database_url(os.environ["DATABASE_URL"])

# Embeddings. "local" = sentence-transformers. "hash" = tests/CI only: deterministic,
# no download, no semantic quality.
EMBEDDING_BACKEND = os.environ.get("EMBEDDING_BACKEND") or "local"
EMBEDDING_MODEL = (
    os.environ.get("EMBEDDING_MODEL") or "paraphrase-multilingual-MiniLM-L12-v2"
)
EMBEDDING_ID = "hash-test" if EMBEDDING_BACKEND == "hash" else EMBEDDING_MODEL

# Retrieval
TOP_K = _int("RETRIEVAL_TOP_K", 4)
CANDIDATES = _int("RETRIEVAL_CANDIDATES", 20)
MIN_SCORE = _float("RETRIEVAL_MIN_SCORE", 0.30)

# Generation. "auto" picks Gemini, then Claude, then extracts-only.
LLM_PROVIDER = (os.environ.get("LLM_PROVIDER") or "auto").lower()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or ""
GEMINI_MODEL = os.environ.get("GEMINI_MODEL") or "gemini-3.8-flash"
GEMINI_BASE_URL = os.environ.get("GEMINI_BASE_URL") or None
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY") or ""
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL") or "claude-haiku-5-5"
LLM_TIMEOUT_SECONDS = _int("LLM_TIMEOUT_SECONDS", 30)

# Public exposure
ALLOWED_ORIGINS = [
    o.strip()
    for o in (os.environ.get("ALLOWED_ORIGINS") or "http://localhost:3000").split(",")
    if o.strip()
]
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN") or ""
RATE_LIMIT_PER_MINUTE = _int("RATE_LIMIT_PER_MINUTE", 20)
MAX_UPLOAD_MB = _int("MAX_UPLOAD_MB", 25)
SEED_SAMPLE = (os.environ.get("SEED_SAMPLE") or "").lower() in {"1", "true", "yes"}
