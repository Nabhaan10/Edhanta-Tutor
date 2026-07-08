# Edhanta AI

Edhanta AI is a **RAG-based** (Retrieval-Augmented Generation) AI tutoring chatbot for Indian board students (CBSE & Maharashtra Board). Students can ask questions in text or upload an image of a question — the system retrieves relevant chunks from ingested textbooks and uses an LLM to generate detailed, exam-oriented answers grounded in the curriculum.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Data Ingestion Pipeline](#data-ingestion-pipeline)
- [Backend Setup](#backend-setup)
- [Frontend Setup](#frontend-setup)
- [Running Locally](#running-locally)
- [Production Handoff Checklist](#production-handoff-checklist)

---

## Architecture Overview

```
[Frontend — TanStack Start / React / Vite]
        |
        | HTTP (JSON / multipart)
        ↓
[Backend — FastAPI]
        |
        ├─ /ask         → RAG pipeline → OpenRouter LLM
        ├─ /ask-image   → Vision extraction → RAG → LLM
        └─ /health
        |
        ├─ ChromaDB (local vector store)
        └─ Sentence-Transformers (embedding model: all-MiniLM-L6-v2)
```

---

## Project Structure

```
edhanta-ai/
├── backend/            # FastAPI app (routes, schemas, logger)
├── rag/                # RAG pipeline modules
│   ├── chatbot.py      # Top-level ask() function
│   ├── retriever.py    # ChromaDB search with threshold filtering
│   ├── generator.py    # OpenRouter LLM generation
│   ├── vision_extractor.py  # Google Gemini image → question extraction
│   ├── router.py       # Classifies query as theory / numerical
│   ├── solver.py       # Step-by-step numerical solver
│   ├── memory.py       # Sliding-window conversation memory
│   ├── chunker.py      # PDF chunking utilities
│   ├── loader.py       # Document loader
│   └── vectordb.py     # ChromaDB client wrapper
├── data/               # Textbook data (raw PDFs, chunks, processed JSON)
├── chroma_db/          # Local ChromaDB vector store (built from data/)
├── frontend/           # React / TanStack Start UI
├── tests/              # Unit & integration tests
├── config.py           # Non-secret configuration (model names, thresholds)
├── requirements.txt    # Pinned Python dependencies
└── .env                # API keys (private repo only — see warning below)
```

---

## Prerequisites

- **Python** 3.10+
- **Node.js** 18+ (or [Bun](https://bun.sh/))
- **pip** / a virtual environment manager

---

## Data Ingestion Pipeline

This step builds the ChromaDB vector store from your raw PDF textbooks.
**Run this once before starting the backend for the first time, and re-run whenever you add new textbooks.**

### Expected folder structure before ingestion

```
data/
└── raw/
    ├── class9_Maths/
    │   └── chapter1.pdf
    ├── class9_Science/
    │   └── chapter1.pdf
    ├── class10_Maths/
    │   └── chapter1.pdf
    └── class10_Science/
        └── chapter1.pdf
```

> **Important:** Subfolder names must follow the pattern `class{N}_{Subject}` (e.g. `class10_Science`).
> The chunker reads this to extract class number and subject metadata for each chunk.

### Step 1 — Extract text from PDFs

Reads all PDFs from `data/raw/` and saves plain-text versions to `data/processed/`.

```bash
python -m rag.loader
```

### Step 2 — Chunk the extracted text

Splits each text file into overlapping chunks (1000 chars, 200 overlap) and saves them as JSON to `data/chunks/`.

```bash
python -m rag.chunker
```

### Step 3 — Embed chunks and store in ChromaDB

Loads every JSON chunk file, generates embeddings using `all-MiniLM-L6-v2`, and upserts them into the local ChromaDB collection.

```bash
python -m rag.vectordb
```

On success you'll see:
```
Loaded <N> chunks
Stored in ChromaDB
```

The `chroma_db/` directory will be created/updated automatically.

---

## Backend Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. (First time) Run the ingestion pipeline — see 'Data Ingestion Pipeline' section above

# 4. Run the backend server
uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at `http://127.0.0.1:8000`.
Interactive docs: `http://127.0.0.1:8000/docs`

---

## Frontend Setup

```bash
cd frontend

# Install dependencies (using npm or bun)
npm install
# or: bun install

# Run the dev server
npm run dev
# or: bun run dev
```

The UI will be available at `http://localhost:8080`.

---

## Running Locally

Start both servers in separate terminals:

```bash
# Terminal 1 — Backend
uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```

Open `http://localhost:8080` in your browser.

---

## Production Handoff Checklist

The following items use localhost/development values and **must be updated before production deployment**:

### 🔴 Required Changes

| File | Location | Current Value | What to Change To |
|------|----------|---------------|-------------------|
| `backend/app.py` | Line ~25 — `allow_origins` | `"http://localhost:8080"` | Add your production frontend URL, e.g. `"https://edhanta.ai"` |
| `frontend/src/routes/index.tsx` | Line ~66 — `/ask` fetch URL | `"http://127.0.0.1:8000/ask"` | Replace with production backend URL |
| `frontend/src/routes/index.tsx` | Line ~133 — `/ask-image` fetch URL | `"http://127.0.0.1:8000/ask-image"` | Replace with production backend URL |
| `config.py` | Line 3 — `OPENROUTER_SITE_URL` | `"https://edhanta.ai"` | Replace with your actual registered domain |

> **Tip:** For a clean approach, replace the hardcoded `http://127.0.0.1:8000` URLs in `index.tsx` with a Vite env variable:
> ```ts
> const API_BASE = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";
> fetch(`${API_BASE}/ask`, ...)
> ```
> Then set `VITE_API_URL=https://your-backend.com` in your deployment environment.

### 🟠 Infrastructure

- **ChromaDB** — Currently uses a local file-based store (`chroma_db/`). For production, migrate to a hosted vector DB (e.g. [Chroma Cloud](https://trychroma.com), Pinecone, or Weaviate).
- **Data files** — Textbooks in `data/` are large. Consider hosting them on S3/GCS and streaming into the vector DB rather than shipping them in the repo.
- **Backend deployment** — Use a production ASGI server behind a reverse proxy:
  ```bash
  uvicorn backend.app:app --host 0.0.0.0 --port 8000 --workers 4
  ```
- **HTTPS** — Ensure both backend and frontend are served over HTTPS in production.

### 🟡 Nice to Have

- Add rate limiting to `/ask` and `/ask-image` endpoints (e.g. `slowapi`).
- Add structured logging / log aggregation (e.g. Datadog, GCP Logging).
- Add a `Dockerfile` for containerised deployment.
