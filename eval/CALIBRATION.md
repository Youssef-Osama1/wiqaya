# Retrieval evaluation & guardrail calibration (Phase 6)

Source run: `eval/runs/retrieval_20260811T171243Z.json` — 18-question golden set
(`eval/golden.jsonl`), real Cohere embeddings (`embed-english-v3.0`) + real
`CohereRerank` (`rerank-v3.5`) against the live `wiqaya_chunks` collection (120 chunks,
both guidelines). Not simulated — every number below came from actual API calls.

## Retrieval matrix

| mode | k | P@k | R@k | MRR | n |
|---|---|---|---|---|---|
| semantic | 3 | 0.231 | 0.615 | 0.526 | 13 |
| semantic | 5 | 0.169 | 0.692 | 0.541 | 13 |
| semantic | 10 | 0.100 | 0.846 | 0.562 | 13 |
| bm25 | 3 | 0.077 | 0.192 | 0.179 | 13 |
| bm25 | 5 | 0.123 | 0.577 | 0.268 | 13 |
| bm25 | 10 | 0.069 | 0.654 | 0.279 | 13 |
| hybrid | 3 | 0.205 | 0.577 | 0.436 | 13 |
| hybrid | 5 | 0.154 | 0.731 | 0.467 | 13 |
| hybrid | 10 | 0.100 | 0.846 | 0.488 | 13 |
| **hybrid_rerank** | 3 | 0.333 | 0.846 | 0.795 | 13 |
| **hybrid_rerank** | **5** | 0.231 | **0.923** | **0.795** | 13 |
| hybrid_rerank | 10 | 0.115 | 0.923 | 0.795 | 13 |

`n=13` is the direct + multi_chunk + 2 answerable-ambiguous questions with a real
`relevant_chunk_ids` set — out-of-scope questions have none by design (nothing can be
"relevant" for them), so they're excluded from P@k/R@k/MRR and used for score-based
calibration instead (below).

## Default mode + k: `hybrid_rerank`, `k=5`

`hybrid_rerank` dominates every other mode at every k — MRR 0.795 vs. semantic's 0.541,
plain hybrid's 0.467, bm25's 0.268 at k=5. `k=5` is the sweet spot: recall@5 (0.923)
already equals recall@10, so k=10 only dilutes precision (0.231 → 0.115) without
finding anything extra. `DEFAULT_TOP_K=5` in `.env.example` was already set to this by
coincidence from Phase 1 — confirmed correct, not changed.

## SIM_HALT_THRESHOLD / SIM_DOWNGRADE_THRESHOLD calibration

Real `hybrid_rerank` top-score distributions (the field these thresholds actually
gate — see the warning below about `hybrid` mode):

```
answerable  (13): 0.487, 0.564, 0.609, 0.669, 0.815, 0.832, 0.884, 0.891, 0.908, 0.917, 0.931, 0.938, 0.956
out_of_scope (4): 0.075, 0.080, 0.083, 0.619
insufficient (1): 0.520
```

3 of 4 out-of-scope questions cluster tightly around 0.08 — clearly separable from
every answerable score. One outlier (0.619) sits inside the answerable range (see
failure analysis below).

- **`SIM_HALT_THRESHOLD = 0.45`** — below the lowest answerable score (0.487) and
  above the tight out-of-scope cluster (~0.08), so a genuinely off-topic query HALTs
  (insufficient evidence, generator never called) while every real answerable question
  still proceeds.
- **`SIM_DOWNGRADE_THRESHOLD = 0.65`** — splits the answerable distribution roughly at
  its first quartile (3/13 scores — 0.487, 0.564, 0.609 — fall below it and get
  confidence capped at Low; the remaining 10/13 keep full confidence). The one
  `insufficient` question (A3, "how long until BP medication works") scores 0.520:
  between the two thresholds, so it PROCEEDS but capped at Low confidence — reasonable,
  since the guidelines don't state a specific onset-of-action time and the generator's
  own `insufficient_evidence` self-report (tier-2 guardrail) is the right place to catch
  that precisely, not the retrieval threshold alone.

These are deliberately round numbers reflecting the real gap in the data, not a curve
fit to 18 points — recalibrate once the golden set grows past v1 (Phase 8).

**Important — these thresholds are only valid for `hybrid_rerank`'s score.** Plain
`hybrid` mode's score is a documented rank-based display proxy (see
`RetrievalController`) — every question's top result scores exactly `1.0` in this run's
data (rank 1 always gets `1.0 - 0/n`), so it carries zero discriminative signal. Never
gate a HALT/DOWNGRADE decision on `hybrid` mode's score; the guardrail stage (Phase 7)
must run its threshold check against `hybrid_rerank`.

## Failure analysis (≥1 documented, both found via real evaluation)

**1. Data-loss bug, found and fixed**: `IngestionController.ingest(doc_key)` defaulted
`fresh=True`, which called `get_vectordb(..., fresh=True)` — a *whole-collection* wipe.
Ingesting WHO then NICE in sequence (exactly what `/api/v1/data/ingest`'s default
multi-doc call does) silently deleted WHO's just-added chunks when NICE's `fresh=True`
ingest ran second. Caught by manually running the real multi-doc ingest and finding
`wiqaya_chunks` had 44 points instead of the expected 120. Fixed with a new
`delete_by_doc_key()` (Qdrant payload filter / PGVector `cmetadata->>'doc_key'` filter)
that scopes deletion to the one doc being re-ingested, plus a doc-scoped
`get_vector_count(..., doc_key=...)` so the post-index assertion is correct once a
collection holds more than one doc. Regression-tested in
`tests/test_ingestion_controller.py::test_ingesting_a_second_doc_does_not_wipe_the_first`
for both backends.

**2. Retrieval failure mode, documented (not code-fixable at this layer)**: O1 ("What
is the recommended first-line treatment for type 2 diabetes?", `out_of_scope`,
expected `refuse`) scored 0.619 with `hybrid_rerank` — its top match was NICE's "Step 1
treatment" rationale chunk, which discusses type 2 diabetes *as a comorbidity relevant
to choosing a hypertension drug*, not as its own treatment topic. The reranker can't
distinguish "mentions X as context" from "is about X" from lexical/semantic overlap
alone. This is exactly why the plan's guardrail design has three independent layers —
the rule-based/LLM input gate (Phase 7) is expected to catch this kind of off-topic
clinical question on its own terms (question intent), independent of what retrieval
happens to score it. A single retrieval-score miss on an edge case is an argument for
defense-in-depth, not a retrieval bug to chase further with 18 data points.
