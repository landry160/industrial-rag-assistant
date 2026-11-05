"""Hybrid retrieval: vector + French full-text + exact equipment/part codes.

Vector search understands paraphrases but is weak on codes like "T88-PROBE-02".
Full-text covers vocabulary. Codes get their own list because PostgreSQL's parser
splits "T-88" into pieces. The three rankings are merged with Reciprocal Rank Fusion.
"""

import re
from dataclasses import dataclass

from app.config import CANDIDATES, EMBEDDING_ID, MIN_SCORE, TOP_K
from app.db import get_db_connection
from app.embeddings import embed

_RRF_K = 60
_CODE = re.compile(r"\b(?=[A-Za-z0-9-]*\d)(?=[A-Za-z0-9-]*[A-Za-z])[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*\b")

_SELECT = (
    "SELECT c.id, d.source, c.page, c.content, c.embedding <=> %(vector)s::vector "
    "FROM document_chunks c JOIN documents d ON d.id = c.document_id "
    "WHERE d.embedding_model = %(model)s "
)
_ORDER_LIMIT = " LIMIT %(limit)s"


@dataclass
class Hit:
    chunk_id: int
    document: str
    page: int | None
    content: str
    score: float  # similarité cosinus
    exact_code: bool = False


def extract_codes(question: str) -> list[str]:
    """'capteur T-88' -> ['T88']. Hyphens are dropped on both sides of the match."""
    return sorted({m.replace("-", "").upper() for m in _CODE.findall(question)})


def rrf_merge(rankings: list[list[int]]) -> dict[int, float]:
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (_RRF_K + rank)
    return scores


def search(question: str, limit: int = TOP_K) -> list[Hit]:
    """Top chunks by hybrid rank, before any relevance threshold."""
    vector = "[" + ",".join(str(x) for x in embed([question])[0]) + "]"
    params = {
        "vector": vector,
        "model": EMBEDDING_ID,
        "limit": CANDIDATES,
        "question": question,
    }
    codes = extract_codes(question)
    params["patterns"] = [f"%{code}%" for code in codes]

    with get_db_connection() as conn:
        by_vector = conn.execute(
            _SELECT + "ORDER BY c.embedding <=> %(vector)s::vector" + _ORDER_LIMIT,
            params,
        ).fetchall()
        lexical = conn.execute(
            _SELECT
            + "AND c.tsv @@ replace(plainto_tsquery('french', %(question)s)::text, "
            "'&', '|')::tsquery "
            "ORDER BY ts_rank(c.tsv, replace(plainto_tsquery('french', "
            "%(question)s)::text, '&', '|')::tsquery) DESC"
            + _ORDER_LIMIT,
            params,
        ).fetchall()
        by_code = (
            conn.execute(
                _SELECT
                + "AND regexp_replace(upper(c.content || ' ' || d.source), "
                "'[^A-Z0-9]', '', 'g') LIKE ANY(%(patterns)s) "
                "ORDER BY c.id" + _ORDER_LIMIT,
                params,
            ).fetchall()
            if codes
            else []
        )

    exact = {row[0] for row in by_code}
    rows = {row[0]: row for row in [*by_vector, *lexical, *by_code]}
    fused = rrf_merge([[r[0] for r in ranking] for ranking in (by_vector, lexical, by_code)])
    ordered = sorted(fused, key=fused.get, reverse=True)[:limit]
    return [
        Hit(
            chunk_id=chunk_id,
            document=rows[chunk_id][1],
            page=rows[chunk_id][2],
            content=rows[chunk_id][3],
            score=round(1 - rows[chunk_id][4], 4),
            exact_code=chunk_id in exact,
        )
        for chunk_id in ordered
    ]


def retrieve(question: str, limit: int = TOP_K, min_score: float = MIN_SCORE) -> list[Hit]:
    """Chunks allowed to back an answer. An empty list means: do not answer."""
    return [
        hit
        for hit in search(question, limit)
        if hit.score >= min_score or hit.exact_code
    ]
