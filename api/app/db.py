
import os
import psycopg
from pgvector.psycopg import register_vector

DATABASE_URL = os.environ["DATABASE_URL"]


def get_db_connection():
    conn = psycopg.connect(DATABASE_URL)
    register_vector(conn)
    return conn


SCHEMA = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chunks_embedding
    ON chunks USING hnsw (embedding vector_cosine_ops);
"""


def init_db():
    # Première connexion : créer l'extension avant register_vector()
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Deuxième connexion : le type vector existe désormais
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id SERIAL PRIMARY KEY,
                    source TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding VECTOR(384) NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_embedding
                ON chunks USING hnsw (embedding vector_cosine_ops);
            """)
