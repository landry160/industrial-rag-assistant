"""Industrial RAG Assistant — API service.

Extension points for the build sessions (marked TODO-1..4):
  TODO-1  Embed the incoming question (embeddings provider).
  TODO-2  Retrieve top-k chunks from pgvector (vector similarity).
  TODO-3  Generate the answer from retrieved passages only (LLM call).
  TODO-4  Ingest: chunk an uploaded document, embed, store in pgvector.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.db import get_db_connection, init_db
from app.embeddings import embed
from app.chunking import chunk_text

app = FastAPI(title="Industrial RAG Assistant API")


class AskRequest(BaseModel):
    question: str


class Source(BaseModel):
    document: str
    section: str
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]


class DocumentIn(BaseModel):
    source: str
    text: str


class IngestRequest(BaseModel):
    documents: list[DocumentIn]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    """Answer a technical question from the indexed documentation."""
    # TODO-1: embed req.question -> query vector
    # TODO-2: pgvector similarity search -> top-k chunks
    # TODO-3: LLM call grounded on retrieved passages -> answer + citations
    raise HTTPException(
        status_code=501,
        detail="RAG pipeline not implemented yet — see TODO-1..3 in api/app/main.py",
    )


@app.post("/ingest")
def ingest(req: IngestRequest) -> dict:
    """Index documents into the vector store: chunk -> embed -> store."""
    init_db()
    rows = []
    for doc in req.documents:
        for chunk in chunk_text(doc.text):
            rows.append((doc.source, chunk))
    vectors = embed([c for _, c in rows])
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO chunks (source, content, embedding) VALUES (%s, %s, %s)",
                [(s, c, v) for (s, c), v in zip(rows, vectors)],
            )
        conn.commit()
    return {"chunks_indexed": len(rows)}
