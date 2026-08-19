# Wiqaya

[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![Qdrant](https://img.shields.io/badge/Qdrant-pgvector-DC244C.svg?logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![Cohere](https://img.shields.io/badge/Cohere-command--a-39594D.svg?logo=cohere&logoColor=white)](https://cohere.com/)

A **clinical decision support RAG system** over the WHO and NICE hypertension guidelines. Ask a clinical question, get an answer where every claim is tied to a verbatim quote, a page number, and a section of the source guideline — or an honest refusal when the evidence cannot carry it.

The design bet: a fluent answer is not a safe answer. Three independent guardrail layers sit between the question and the output, and any one of them can stop or downgrade the response.

**[Live demo](https://wiqaya-web.onrender.com/)** — ask a question, inspect the full evidence trail behind the answer.

---

## Demo

<video src="https://github.com/user-attachments/assets/2354b895-80c2-4bfe-837d-163a94e5dce5" controls width="100%"></video>

Ask, inspect the retrieved evidence, watch the safety gate refuse an out-of-scope question, and read the measured evaluation numbers on the dashboard.

---

## Features

- **Three-layer guardrail pipeline** — an input gate, calibrated retrieval thresholds, and a post-generation claim audit, each able to stop the answer on its own
- **Verifiable citations** — every quote in the final answer is checked verbatim against its source chunk; a quote that fails verification is dropped, and its citation with it
- **Four retrieval modes** — semantic, BM25, hybrid, and hybrid + Cohere rerank, switchable per request from the UI
- **Guideline-aware chunking** — NICE recommendations are kept atomic and never split; WHO prose is packed by sentence, both bounded by document section
- **Measured, not claimed** — a 25-question golden set with anchor texts verified against the real corpus, scored on Recall/Precision/MRR, citation accuracy, unsupported-claim rate, and refusal correctness
- **Pluggable providers** — OpenAI or Cohere, Qdrant or pgvector, all selected from config through factories rather than code changes
- **Full trace UI** — recommendation, evidence quotes, citations, confidence and audit detail, raw retrieval, and per-stage timings for every question
- **Voice in and out** — speak a question, hear the recommendation read back, where the browser supports it

---

## How it works

A question moves through five stages, and three of them can stop it:

1. **Layer 1 · Input gate** — deterministic regex rules run first and for free (emergency symptoms, out-of-domain topics, personal-dosing phrasing); anything that falls through goes to an LLM classifier returning `ALLOW` / `CAUTION` / `REFUSE`. A refusal short-circuits everything: retrieval never runs.
2. **Retrieval** — vector search and BM25 combine into 20 candidates, then Cohere rerank cuts them to the top 5.
3. **Layer 2 · Score thresholds** — a top score below `0.45` halts the request before generation; below `0.65` it proceeds with confidence capped at Low.
4. **Generation** — structured output, grounded strictly in the retrieved excerpts, each tagged with its chunk id.
5. **Layer 3 · Claim audit** — tier 1 checks every cited quote appears verbatim in its source chunk; tier 2 has the model verify each factual claim against the retrieved text. Quotes that fail are dropped from the answer, and their citations with them.

The layers are deliberately independent. Evaluation caught a case where retrieval alone was fooled — *"first-line treatment for type 2 diabetes"* scored 0.619, because NICE discusses diabetes as a comorbidity when choosing an antihypertensive — but the input gate rejected it correctly on question intent. That is the whole argument for defense in depth.

Confidence is derived, never guessed: **High** when the gate allows, the score clears both thresholds, and the audit is clean; **Medium** when the gate flags a personal-advice framing; **Low** on a downgraded score, an unsupported claim, or a failed quote check; **Insufficient Evidence** when the score halts or the model itself reports it cannot answer.

The two similarity thresholds are calibrated from real score distributions, not picked by feel — see [`eval/CALIBRATION.md`](eval/CALIBRATION.md).

---

## Corpus

| Document | Pages | Chunks |
|---|---|---|
| [WHO Guideline for the Pharmacological Treatment of Hypertension in Adults](https://www.who.int/publications/i/item/9789240033986) | 61 | 76 |
| [NICE NG136: Hypertension in Adults — Diagnosis and Management](https://www.nice.org.uk/guidance/ng136) | 52 | 44 |

Both PDFs are parsed with PyMuPDF, cleaned per document, mapped to sections from the PDF table of contents, and packed into ~600-token chunks with stable content-addressed ids (`nice_ng136-p016-beee1ff3` = document, source page, content hash). The cleaned pages and chunks are committed as JSONL, so retrieval and BM25 work from a clean checkout.

---

## Evaluation

End-to-end run over the full golden set, `hybrid_rerank` at k=5, real Cohere backends:

| Metric | Value |
|---|---|
| Recall@5 | 0.889 |
| MRR | 0.769 |
| Precision@5 | 0.222 |
| Citation accuracy | 0.977 |
| Unsupported claim rate | **0.000** |
| Refusal correctness (out of scope) | **1.000** |
| Behavioral correctness | 24 / 25 |

`hybrid_rerank` dominates every other mode at every k (MRR 0.769 against 0.531 hybrid, 0.557 semantic, 0.371 BM25), and recall@5 already equals recall@10, so a larger k only dilutes precision. Precision@5 is structurally low by design: chunks bundle several adjacent NICE recommendations, so retrieving 5 pulls in relevant-but-unlabelled neighbours even when the labelled chunk ranks first.

Full write-ups in [`eval/CALIBRATION.md`](eval/CALIBRATION.md) and [`eval/E2E_ANALYSIS.md`](eval/E2E_ANALYSIS.md).

---

## Architecture

Strict one-directional layering, `routes → controllers → stores + core`:

```
src/
├── routes/         HTTP layer (thin FastAPI handlers + request/response schemas)
├── controllers/    Orchestration (Ingestion, Retrieval, Gate, Answer, Evaluation)
├── stores/         Provider factories (llm, embeddings, reranker, bm25, vector db)
├── core/           Framework-free, hand-built, unit-tested logic
│   ├── ingestion/    PDF cleaning, TOC section mapping
│   ├── chunking/     token-aware packer, atomic units, stable chunk ids
│   ├── generation/   context assembly, grounded chain, citations, confidence
│   ├── guardrails/   gate rules, classifier, thresholds, claim audit
│   ├── evaluation/   metrics, golden-set loading and validation
│   └── schemas.py    single source of truth for every domain model
└── helpers/        Pydantic Settings (env-driven configuration)

eval/               golden set, evaluation runners, calibration write-ups
frontend/           React + Vite + TypeScript UI
docker/             pgvector + Qdrant compose stack
```

Every external dependency sits behind a factory that reads `Settings` and builds the right LangChain object at startup, so swapping a provider is a config change. `core/` imports no web framework and no vendor SDK beyond the parsing libraries, which is what makes the retrieval, guardrail, and chunking logic cheap to test in isolation.

**Stack:** FastAPI · LangChain · Cohere (`command-a-03-2025`, `embed-english-v3.0`, `rerank-v3.5`) · Qdrant / pgvector · rank_bm25 · PyMuPDF · React 19 + Vite + Tailwind + shadcn/ui · TanStack Query · Docker Compose · Render

---

## Quickstart

### Prerequisites

- Docker Desktop running
- Python 3.11+ and Node 20+
- A [Cohere API key](https://dashboard.cohere.com/) (free trial tier works)

### 1. Set up

```bash
git clone https://github.com/Youssef-Osama1/wiqaya
cd wiqaya
conda create -n wiqaya python=3.11 -y
conda activate wiqaya
pip install -r requirements.txt

cp .env.example .env      # fill in COHERE_API_KEY
```

### 2. Start the vector stores

Both come up together; `VECTOR_DB_BACKEND` in `.env` decides which one is used.

```bash
docker compose -f docker/docker-compose.yml up -d    # pgvector :5500, Qdrant :6333
```

### 3. Run the API and index the corpus

```bash
uvicorn src.main:app --reload
curl -X POST localhost:8000/api/v1/data/ingest -H "Content-Type: application/json" -d '{}'
```

Interactive API docs at `/docs`.

### 4. Run the UI

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

---

## Disclaimer

Wiqaya is a prototype clinical decision support system. It summarizes published guideline text and does not replace professional medical judgment, local protocols, or the current full guideline. It must not be used to diagnose, prescribe, or make decisions about the care of any individual patient.
