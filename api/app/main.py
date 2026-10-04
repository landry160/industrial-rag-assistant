"""Industrial RAG Assistant — API service.

Extension points for the build sessions (marked TODO-1..4):
  TODO-1  Embed the incoming question (embeddings provider).
  TODO-2  Retrieve top-k chunks from pgvector (vector similarity).
  TODO-3  Generate the answer from retrieved passages only (LLM call).
  TODO-4  Ingest: chunk an uploaded document, embed, store in pgvector.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel

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
async def ingest(file: UploadFile = File(...)) -> dict:
    """Index a document (PDF/manual/procedure) into the vector store."""
    # TODO-4: parse file -> chunk by section with overlap -> embed -> store
    raise HTTPException(
        status_code=501,
        detail="Ingestion not implemented yet — see TODO-4 in api/app/main.py",
    )
