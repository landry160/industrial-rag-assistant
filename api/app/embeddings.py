"""Local embeddings (384 dims). No document text leaves the server at this step."""

import hashlib
import math
import re
from functools import lru_cache

from app.config import EMBEDDING_BACKEND, EMBEDDING_MODEL

DIM = 384


@lru_cache(maxsize=1)
def _model():
    # Import tardif : torch est lourd et inutile avec le backend "hash".
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL)


def _hash_embed(text: str) -> list[float]:
    """Deterministic bag-of-words vector, for tests and CI only."""
    vector = [0.0] * DIM
    for token in re.findall(r"\w+", text.lower()):
        digest = hashlib.sha256(token.encode()).digest()
        index = int.from_bytes(digest[:4], "big") % DIM
        vector[index] += 1.0 if digest[4] % 2 else -1.0
    norm = math.sqrt(sum(x * x for x in vector)) or 1.0
    return [x / norm for x in vector]


def embed(texts: list[str]) -> list[list[float]]:
    if EMBEDDING_BACKEND == "hash":
        return [_hash_embed(t) for t in texts]
    vectors = _model().encode(texts, normalize_embeddings=True)
    if vectors.shape[1] != DIM:
        raise ValueError(
            f"Le modèle produit {vectors.shape[1]} dimensions, {DIM} attendues."
        )
    return vectors.tolist()
