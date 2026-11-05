"""PostgreSQL + pgvector access and schema."""

import logging
import time

import psycopg
from pgvector.psycopg import register_vector

from app.config import DATABASE_URL
from app.embeddings import DIM

log = logging.getLogger(__name__)

# Tables neuves : l'ancienne table `chunks` n'a ni page, ni document parent. Elle est
# laissée intacte et ignorée; il suffit de réindexer les documents.
SCHEMA = f"""
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL UNIQUE,
    sha256 TEXT NOT NULL,
    pages INTEGER,
    embedding_model TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    page INTEGER,
    content TEXT NOT NULL,
    embedding VECTOR({DIM}) NOT NULL,
    tsv TSVECTOR GENERATED ALWAYS AS (to_tsvector('french', content)) STORED
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
    ON document_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_document_chunks_tsv
    ON document_chunks USING gin (tsv);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document
    ON document_chunks (document_id);
"""


def get_db_connection():
    conn = psycopg.connect(DATABASE_URL)
    register_vector(conn)
    return conn


def init_db(attempts: int = 30, delay: float = 1.0) -> None:
    """Create the schema, waiting for the database to accept connections."""
    for attempt in range(1, attempts + 1):
        try:
            # L'extension doit exister avant register_vector().
            with psycopg.connect(DATABASE_URL) as conn:
                conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            break
        except psycopg.OperationalError:
            if attempt == attempts:
                raise
            log.info("Base de données pas encore prête (%s/%s)", attempt, attempts)
            time.sleep(delay)

    with get_db_connection() as conn:
        conn.execute(SCHEMA)
