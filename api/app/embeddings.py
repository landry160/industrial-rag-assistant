import os
"""Embeddings 100 % locaux — modèle all-MiniLM-L6-v2, 384 dims."""
from functools import lru_cache

from sentence_transformers import SentenceTransformer

DIM = 384


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer("all-MiniLM-L6-v2")


def embed(texts: list[str]) -> list[list[float]]:
    vectors = _model().encode(texts, normalize_embeddings=True)
    assert vectors.shape[1] == DIM, f"dimension {vectors.shape[1]} != {DIM}"
    return vectors.tolist()
