"""Chunk -> embed -> store. Re-ingesting a source replaces it."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

from app.chunking import chunk_text
from app.config import EMBEDDING_ID
from app.db import get_db_connection
from app.embeddings import embed
from app.parsing import Section


@dataclass
class IngestResult:
    source: str
    chunks_indexed: int
    status: str  # "created" | "updated" | "unchanged"


def clean_source_name(filename: str) -> str:
    return Path(filename.replace("\\", "/")).name[:255] or "document"


def ingest_sections(source: str, sections: list[Section], raw: bytes) -> IngestResult:
    source = clean_source_name(source)
    sha256 = hashlib.sha256(raw).hexdigest()

    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT id, sha256, embedding_model FROM documents WHERE source = %s",
            (source,),
        ).fetchone()
    if row and row[1] == sha256 and row[2] == EMBEDDING_ID:
        return IngestResult(source, 0, "unchanged")

    rows = [
        (section.page, chunk)
        for section in sections
        for chunk in chunk_text(section.text)
    ]
    title = Path(source).stem.replace("-", " ").replace("_", " ")
    # Le titre situe un passage isolé (« la courroie » de quel équipement ?).
    vectors = embed([f"{title} : {chunk}" for _, chunk in rows])
    pages = max((s.page for s in sections if s.page), default=None)

    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM documents WHERE source = %s", (source,))
        cur.execute(
            "INSERT INTO documents (source, sha256, pages, embedding_model) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (source, sha256, pages, EMBEDDING_ID),
        )
        document_id = cur.fetchone()[0]
        cur.executemany(
            "INSERT INTO document_chunks "
            "(document_id, position, page, content, embedding) "
            "VALUES (%s, %s, %s, %s, %s::vector)",
            [
                (document_id, position, page, chunk, str(vector).replace(" ", ""))
                for position, ((page, chunk), vector) in enumerate(zip(rows, vectors))
            ],
        )
    return IngestResult(source, len(rows), "updated" if row else "created")


def list_documents() -> list[dict]:
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT d.id, d.source, d.pages, d.created_at, d.embedding_model, "
            "       COUNT(c.id) "
            "FROM documents d LEFT JOIN document_chunks c ON c.document_id = d.id "
            "GROUP BY d.id ORDER BY d.created_at DESC, d.id DESC"
        ).fetchall()
    return [
        {
            "id": doc_id,
            "source": source,
            "pages": pages,
            "created_at": created_at.isoformat(),
            "chunks": chunks,
            "needs_reindex": model != EMBEDDING_ID,
        }
        for doc_id, source, pages, created_at, model, chunks in rows
    ]


def delete_document(document_id: int) -> bool:
    with get_db_connection() as conn:
        cursor = conn.execute("DELETE FROM documents WHERE id = %s", (document_id,))
        return cursor.rowcount > 0
