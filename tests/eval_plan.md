# Step 11 — Evaluation Plan

## 11.1 Gold Queries (10–15)
Use/extend `tests/baseline_queries.json`. Add coverage for:
- Skills combos (python+aws, docker+postgres)
- Domains (healthcare, ecommerce, backend, analytics)
- Availability (available, soon, unavailable)
- Min years (3+, 5+, 8+)

## 11.2 Metrics
- Retrieval@k (k=3,5): at least one “correct” profile in top-k (binary).
- Human helpfulness (1–5): Does top-1 look like a good match given the query?
- Precision note (qualitative): Are reasons accurate and grounded?

## 11.3 Latency
Record per query:
- Retrieval time (baseline/semantic/hybrid), ms
- (Later) Generation time, ms
Target: local ≤3s retrieval; hybrid+gen ≤5s total.

## 11.4 Logging
Maintain `tests/eval_log.md` (or CSV) with:

| # | Query | Top-k contains correct? (k=3/5) | Human (1–5) | Retr (ms) | Gen (ms) | Notes |
|---|-------|----------------------------------|-------------|-----------|----------|-------|

**Correctness rule:** a “correct” profile has ≥1 requested skill AND domain (if specified); meets min years; respects availability if specified.
