# Deploying Wiqaya to Render

Two Render services plus a managed Qdrant. `render.yaml` in the repo root declares both
services; the five secrets it marks `sync: false` are set by hand so they never enter git.

## 1. Create the vector database

Render's free Postgres is deleted 30 days after creation, so the corpus lives in Qdrant
Cloud instead.

1. Create a free cluster at <https://cloud.qdrant.io> (1 GB RAM / 4 GB disk, no card).
2. Copy the **cluster URL** and an **API key**.

A free cluster suspends after a week of inactivity and is deleted after four, so open the
Qdrant dashboard occasionally if the demo needs to stay alive.

## 2. Deploy the blueprint

In Render: **New → Blueprint**, point it at this repository. It reads `render.yaml` and
creates `wiqaya-api` (Python web service) and `wiqaya-web` (static site).

Render will ask for the values marked `sync: false`. Set them on **wiqaya-api**:

| Variable | Value |
| --- | --- |
| `COHERE_API_KEY` | your Cohere key |
| `QDRANT_URL` | the Qdrant Cloud cluster URL |
| `QDRANT_API_KEY` | the Qdrant Cloud API key |
| `CORS_ORIGINS` | `https://wiqaya-web.onrender.com` (the static site's real URL) |

and on **wiqaya-web**:

| Variable | Value |
| --- | --- |
| `VITE_API_BASE_URL` | `https://wiqaya-api.onrender.com/api/v1` |

The two URLs only exist once Render has created the services, so expect to fill these in,
then trigger one redeploy of each service.

`VITE_API_BASE_URL` is read at build time, not run time: changing it requires a redeploy of
the static site, not just a restart.

## 3. Build the index once

The deployed API starts with an empty Qdrant collection. Ingest the corpus once, against
the deployed API rather than locally:

```bash
curl -X POST https://wiqaya-api.onrender.com/api/v1/data/ingest \
  -H "Content-Type: application/json" -d '{}'
```

The PDFs and pre-chunked JSONL are committed, so this re-embeds and indexes them; it does
not re-parse anything from scratch. It takes a few minutes and consumes Cohere embedding
calls. Verify with a retrieval-only call, which needs no generation:

```bash
curl -X POST https://wiqaya-api.onrender.com/api/v1/nlp/search \
  -H "Content-Type: application/json" \
  -d '{"query":"blood pressure target","mode":"hybrid_rerank","k":3}'
```

## Known limits of the free tier

- **The API sleeps after 15 minutes idle** and takes 30-60 s to wake. Open the site a few
  minutes before demoing so the first judge doesn't meet a cold start.
- **The Cohere key is trial tier** (10 calls/min). Fine for a link people try occasionally;
  several simultaneous questions will hit the limit.
- **The filesystem is ephemeral**: Render wipes anything written at runtime every time a
  free service redeploys, restarts, *or spins down*. An evaluation triggered from the
  deployed dashboard is therefore gone within about fifteen idle minutes, which is why one
  real run (`eval/runs/e2e_20260819T091041Z.json`) is committed and ships with every
  deploy. The dashboard reads it on load, so the numbers are there before anyone clicks
  anything. To refresh it, run the eval locally and commit the newer report.
