# Baseline Search — Evaluation Log (v1)

## Execution plan
1) Normalize (per config/normalization.json)
2) Extract & apply filters (min years, availability, domains)
3) Compute keyword score; collect top_k (per config/baseline.yaml)
4) Record one-line verdict: ✓ / ✗ and why

## Results

| # | Query                                   | Pass/Fail | Notes / Why |
|---|-----------------------------------------|-----------|-------------|
| 1 | python aws 3+ years ecommerce           |           |             |
| 2 | react native mobile app 4+ years        |           |             |
| 3 | available healthcare nlp                |           |             |
| 4 | backend docker postgres                 |           |             |
| 5 | computer vision retail                  |           |             |
| 6 | azure databricks pyspark 5+             |           |             |
| 7 | frontend typescript next.js             |           |             |
| 8 | gcp bigquery dbt marketing analytics    |           |             |

## Improvements list
- [ ] Add alias "rn" → "react native"
- [ ] Consider raising `weights.skills` from 3 → 4
- [ ] Map token "mobile" → domain "mobile"
- [ ] Add alias "cv" → "computer vision"
