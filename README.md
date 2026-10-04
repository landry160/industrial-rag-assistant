# Industrial RAG Assistant

A full-stack AI application that answers technical questions from industrial documentation — equipment manuals, maintenance procedures, datasheets — using retrieval-augmented generation (RAG) with cited sources.

Built by **Landry Tchouela** — Software Engineer, AI & Intelligent Systems.

## The problem

On the plant floor and in engineering offices, answers live inside PDFs: equipment manuals, maintenance procedures, safety sheets. Keyword search misses context; asking a raw LLM invents answers. This project grounds every answer in your own documents — no answer without a source.

## How it works

1. **Ingest** — documents are chunked, embedded, and stored in PostgreSQL with pgvector.
2. **Retrieve** — a question is embedded and matched against the most relevant chunks by vector similarity.
3. **Generate** — an LLM drafts the answer strictly from the retrieved passages, with source citations.

```
Browser (Next.js) → REST API (FastAPI) → PostgreSQL + pgvector → LLM
```

## Stack

- **Frontend:** Next.js (React) — question UI with cited answers
- **API:** FastAPI (Python) — ingestion, retrieval, and generation endpoints
- **Data:** PostgreSQL 16 + pgvector — document chunks and embeddings
- **Infra:** Docker Compose — one command to run everything locally

## Status

🚧 **Day-one scaffold.** Service boundaries, the data model, and the API contracts are in place; the RAG pipeline (ingestion → retrieval → generation) is under active construction.

**Roadmap:** document ingestion pipeline → retrieval tuning and evaluation → cited-answer UI → public deployment with CI/CD.

## Quickstart

Prerequisites: Docker.

```bash
cp .env.example .env   # then fill in your keys
docker compose up --build
```

- Web UI: http://localhost:3000
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Repository map

```
├── docker-compose.yml   # db (pgvector) + api + web
├── api/                 # FastAPI service
│   ├── app/main.py      # /health, /ask, /ingest (+ marked extension points)
│   ├── requirements.txt
│   └── Dockerfile
├── web/                 # Next.js frontend
│   └── app/page.jsx     # question form wired to POST /ask
└── .env.example         # required environment variables (no secrets committed)
```

## API contracts (v1)

- `GET /health` → `{"status": "ok"}`
- `POST /ask` `{ "question": "..." }` → `{ "answer": "...", "sources": [...] }`
- `POST /ingest` (multipart file) → `{ "chunks_indexed": N }`
