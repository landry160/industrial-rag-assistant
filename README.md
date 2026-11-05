# Industrial RAG Assistant

A full-stack AI application that answers technical questions from industrial documentation (equipment manuals, maintenance procedures, datasheets) using retrieval-augmented generation, with every answer tied to its source passages.

Built by **Landry Tchouela**, computer engineering student at the Université de Sherbrooke.

## The problem

On the plant floor and in engineering offices, answers live inside PDFs. Keyword search misses context, and a raw LLM invents answers. This project grounds every answer in your own documents: **no answer without a source**.

## How it works

```
Browser (Next.js) → REST API (FastAPI) → PostgreSQL + pgvector
                                       → LLM (Gemini or Claude)
```

1. **Ingest:** a PDF, TXT or MD file is split on paragraphs and sentences, embedded locally, and stored with its page number.
2. **Retrieve:** three rankings are merged with Reciprocal Rank Fusion: vector similarity for paraphrases, French full-text search for vocabulary, and exact matching for equipment and part codes (`T-88`, `T88-PROBE-02`), which embeddings handle poorly.
3. **Generate:** the LLM answers only from the retrieved passages and cites them as `[n]`.
4. **Verify:** the API checks the citations instead of trusting them. Invented references are removed, and an answer with no valid citation is discarded in favour of the original passages.

## Design decisions

- **Abstention is a feature.** Below the similarity threshold the LLM is not called at all, and the model can also decline with a dedicated token. The UI then tells the user the information is not in the documents.
- **Works without an API key.** With no key, or when the provider is down, the app shows the most relevant passages unchanged, and says so.
- **Documents stay local at the embedding step.** Only the retrieved passages are sent to the LLM.
- **Passages are treated as data.** The system prompt tells the model to ignore instructions found inside documents.
- **Re-ingestion is safe.** An identical file is skipped, and a new version replaces the old chunks.

## Stack

- **Frontend:** Next.js, React, Tailwind CSS, responsive light and dark themes, French UI
- **API:** FastAPI (Python), pypdf, sentence-transformers
- **Data:** PostgreSQL 16 with pgvector (HNSW) and full-text search (GIN)
- **LLM:** Gemini by default, Claude as an alternative, selected from environment variables
- **Infra:** Docker Compose, GitHub Actions

## Quickstart

Prerequisite: Docker.

```bash
cp .env.example .env   # add GEMINI_API_KEY (optional, see above)
docker compose up --build
```

- Web UI: http://localhost:3000
- API docs: http://localhost:8000/docs

Open the web UI and choose **Essayer avec les exemples** to load three sample documents.

## Tests and evaluation

```bash
cd api
pip install -r requirements-dev.txt
DATABASE_URL=postgresql://rag:rag@localhost:5432/rag_test pytest
```

Tests run against a real PostgreSQL with pgvector. The Gemini and Claude SDKs run for real against local fake servers, so no key is needed.

Retrieval quality is measured on a small golden set in `api/eval/golden.json`:

```bash
docker compose exec api python -m eval.evaluate
```

It prints Hit@1, Hit@k and MRR, then a threshold sweep used to choose `RETRIEVAL_MIN_SCORE`. CI runs the same evaluation with the real embedding model.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | `{"status": "ok"}` |
| `GET` | `/config` | Active engine and upload limits, no secrets |
| `POST` | `/ask` | `{ "question": "..." }` → `{ "answer", "sources", "grounded", "mode", "notice" }` |
| `POST` | `/ingest` | Multipart file → `{ "chunks_indexed", "source", "status" }` |
| `POST` | `/ingest/json` | Raw text documents, for scripts |
| `POST` | `/ingest/sample` | Load the sample corpus |
| `GET` | `/documents` | List indexed documents |
| `DELETE` | `/documents/{id}` | Remove a document and its chunks |

## Public deployment

A host that runs Docker is required, because the API needs Python and PostgreSQL with pgvector. In `.env`, set `ADMIN_TOKEN`, `ALLOWED_ORIGINS` and `NEXT_PUBLIC_API_URL`, then:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Questions stay open and rate limited, while adding or deleting documents requires the access code. The sample corpus is loaded at startup. Put a reverse proxy with HTTPS in front of ports 3000 and 8000.

## Repository map

```
├── docker-compose.yml       # db (pgvector) + api + web
├── docker-compose.prod.yml  # public deployment overlay
├── .github/workflows/ci.yml # tests, evaluation, image builds
├── api/
│   ├── app/
│   │   ├── main.py          # routes, access control
│   │   ├── parsing.py       # PDF, TXT, MD to text
│   │   ├── chunking.py      # paragraph and sentence aware chunks
│   │   ├── ingestion.py     # chunk, embed, store, replace
│   │   ├── retrieval.py     # hybrid search and rank fusion
│   │   └── generate.py      # providers, citation checks, abstention
│   ├── eval/                # golden set and evaluation
│   └── tests/
└── web/
    ├── app/                 # layout, theme tokens, page shell
    ├── components/          # assistant, documents, appearance
    └── lib/                 # API client, theme
```
