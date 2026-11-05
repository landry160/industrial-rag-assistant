"""Industrial RAG Assistant — API service."""

import json
import logging
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from app import config
from app.db import init_db
from app.generate import active_model, active_provider, generate_answer
from app.ingestion import IngestResult, delete_document, ingest_sections, list_documents
from app.parsing import ALLOWED_EXTENSIONS, Section, UnsupportedDocument, parse_document
from app.ratelimit import RateLimiter
from app.retrieval import retrieve

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

SAMPLE_CORPUS = Path(__file__).resolve().parent.parent / "data" / "sample_corpus.json"
limiter = RateLimiter(config.RATE_LIMIT_PER_MINUTE)


def ingest_sample() -> list[IngestResult]:
    corpus = json.loads(SAMPLE_CORPUS.read_text(encoding="utf-8"))
    return [
        ingest_sections(
            doc["source"],
            [Section(page=None, text=doc["text"])],
            doc["text"].encode("utf-8"),
        )
        for doc in corpus["documents"]
    ]


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    if config.SEED_SAMPLE:
        ingest_sample()
    yield


app = FastAPI(title="Industrial RAG Assistant API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-Admin-Token"],
)


@app.exception_handler(psycopg.OperationalError)
async def database_unavailable(_: Request, exc: psycopg.OperationalError):
    log.error("Base de données injoignable : %s", exc)
    return JSONResponse(
        status_code=503,
        content={"detail": "La base de données est injoignable pour le moment."},
    )


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    """Writes are open locally and closed as soon as ADMIN_TOKEN is set."""
    if config.ADMIN_TOKEN and not secrets.compare_digest(
        (x_admin_token or "").encode(), config.ADMIN_TOKEN.encode()
    ):
        raise HTTPException(status_code=401, detail="Code d'accès requis ou invalide.")


def rate_limited(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    if not limiter.allow(client):
        raise HTTPException(
            status_code=429,
            detail="Trop de questions en peu de temps. Réessayez dans une minute.",
        )


class AskRequest(BaseModel):
    question: str = Field(max_length=1000)

    @field_validator("question")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("La question est trop courte.")
        return value


class Source(BaseModel):
    id: int
    document: str
    page: int | None
    section: str
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    grounded: bool
    mode: str
    notice: str | None = None


class DocumentIn(BaseModel):
    source: str = Field(min_length=1, max_length=255)
    text: str = Field(min_length=1)


class IngestRequest(BaseModel):
    documents: list[DocumentIn] = Field(min_length=1)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/config")
def public_config() -> dict:
    return {
        "provider": active_provider(),
        "model": active_model(),
        "embedding_model": config.EMBEDDING_ID,
        "writes_protected": bool(config.ADMIN_TOKEN),
        "max_upload_mb": config.MAX_UPLOAD_MB,
        "extensions": sorted(ALLOWED_EXTENSIONS),
    }


@app.post("/ask", response_model=AskResponse, dependencies=[Depends(rate_limited)])
def ask(req: AskRequest) -> AskResponse:
    """Hybrid retrieval, then a grounded answer whose citations are verified."""
    result = generate_answer(req.question, retrieve(req.question))
    return AskResponse(
        answer=result.answer,
        sources=[
            Source(
                id=n,
                document=hit.document,
                page=hit.page,
                section=hit.content,
                score=hit.score,
            )
            for n, hit in enumerate(result.hits, start=1)
        ],
        grounded=result.grounded,
        mode=result.mode,
        notice=result.notice,
    )


@app.post("/ingest", dependencies=[Depends(require_admin)])
def ingest(file: UploadFile) -> dict:
    """Index one uploaded PDF, TXT or MD file."""
    limit = config.MAX_UPLOAD_MB * 1024 * 1024
    data = file.file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(
            status_code=413,
            detail=f"Fichier trop volumineux (maximum {config.MAX_UPLOAD_MB} Mo).",
        )
    name = file.filename or "document.txt"
    try:
        sections = parse_document(name, data)
    except UnsupportedDocument as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    result = ingest_sections(name, sections, data)
    return {
        "chunks_indexed": result.chunks_indexed,
        "source": result.source,
        "status": result.status,
    }


@app.post("/ingest/json", dependencies=[Depends(require_admin)])
def ingest_json(req: IngestRequest) -> dict:
    """Index raw text documents, for scripts."""
    results = [
        ingest_sections(
            doc.source, [Section(page=None, text=doc.text)], doc.text.encode("utf-8")
        )
        for doc in req.documents
    ]
    return {"chunks_indexed": sum(r.chunks_indexed for r in results)}


@app.post("/ingest/sample", dependencies=[Depends(require_admin)])
def ingest_sample_route() -> dict:
    results = ingest_sample()
    return {
        "chunks_indexed": sum(r.chunks_indexed for r in results),
        "documents": len(results),
    }


@app.get("/documents")
def documents() -> dict:
    return {"documents": list_documents()}


@app.delete("/documents/{document_id}", dependencies=[Depends(require_admin)])
def remove_document(document_id: int) -> dict:
    if not delete_document(document_id):
        raise HTTPException(status_code=404, detail="Ce document n'existe plus.")
    return {"deleted": True}
