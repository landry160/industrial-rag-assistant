"""Industrial RAG Assistant — API service.

Extension points for the build sessions (marked TODO-1..4):
  TODO-1  Embed the incoming question (embeddings provider).
  TODO-2  Retrieve top-k chunks from pgvector (vector similarity).
  TODO-3  Generate the answer from retrieved passages only (LLM call).
  TODO-4  Ingest: chunk an uploaded document, embed, store in pgvector.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.generate import generate_answer
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
    """Full RAG: embed question -> retrieve top-k -> generate grounded answer."""
    qv = embed([req.question])[0]
    qv_str = "[" + ",".join(str(x) for x in qv) + "]"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT source, content, embedding <=> %s::vector AS dist "
                "FROM chunks ORDER BY dist LIMIT 3",
                (qv_str,),
            )
            rows = cur.fetchall()
    passages = [(src, content) for src, content, _ in rows]
    sources = [
        Source(document=src, section=content[:80], score=round(1 - dist, 4))
        for src, content, dist in rows
    ]
    answer = generate_answer(req.question, passages)
    return AskResponse(answer=answer, sources=sources)




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
