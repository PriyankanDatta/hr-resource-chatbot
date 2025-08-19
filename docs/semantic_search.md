# Semantic Search & Hybrid (v1)

## 9.1 Embedding Granularity (Decision)
- **Choice:** Per-employee profile blob (1 vector per employee).
- **Blob fields (normalized):** name; skills (comma-joined); projects (comma-joined);
  domains (comma-joined); experience_years (as words); availability.
- **Why:** Simple, fast to build/search; easy to explain “why matched”.

## 9.2 Index Build Outputs
- FAISS index file: `data/employee_index.faiss`
- Metadata mapping: `data/employee_meta.json` (row_id → {employee_id, name, top_fields})
- Stats: `data/employee_index.stats.json` (model, dim, N, timestamp, index type)
- **Embedding model:** `text-embedding-3-large` (configurable)

## 9.3 Query-Time Semantic Path
1) Normalize query (same rules as baseline).
2) Embed query with the same model.
3) Search FAISS → top-k row_ids.
4) Hydrate row_ids → employee metadata (and/or full record).
5) Return `{id, name, sem_score}`.

## 9.4 Hybrid Scoring
- Normalize keyword score: `kw_norm = kw_score / kw_max` (if `kw_max==0`, use 1).
- **Formula (v1):**
- hybrid_score = 0.6 * sem_score + 0.4 * kw_norm
- Return top-k with: `id, name, sem_score, kw_score, kw_norm, hybrid_score, reason`.

## 9.5 Validation
- Reuse `tests/baseline_queries.json`.
- Log results in `tests/semantic_eval.md`:
- Top changes vs baseline, Better? (✓/✗), Notes.
- **Pass criteria:** ≥5/8 queries improved or tied in top-3 relevance; latency acceptable locally.

## Operational Notes
- Rebuild index when employees.json or normalization config changes.
- Keep model choice/dimension in README “Technical Decisions”.
