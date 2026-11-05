"""Tests run against a real PostgreSQL + pgvector, with deterministic embeddings."""

import os

os.environ.setdefault("DATABASE_URL", "postgresql://rag:rag@127.0.0.1:5432/rag_test")
os.environ["EMBEDDING_BACKEND"] = "hash"
os.environ["RETRIEVAL_MIN_SCORE"] = "0.1"
os.environ["RATE_LIMIT_PER_MINUTE"] = "0"
os.environ["LLM_PROVIDER"] = "auto"
os.environ.pop("GEMINI_API_KEY", None)
os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ.pop("ADMIN_TOKEN", None)

import pytest
from fastapi.testclient import TestClient

from app.db import get_db_connection
from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clean_database(client):
    with get_db_connection() as conn:
        conn.execute("TRUNCATE documents RESTART IDENTITY CASCADE")
    yield


@pytest.fixture
def sample(client):
    response = client.post("/ingest/sample")
    assert response.status_code == 200
    return response.json()
