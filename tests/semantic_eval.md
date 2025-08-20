# Semantic Search Evaluation (Step 9.5)

## Queries Tested
(reuse the same 8 from baseline)

1. python aws 3+ years ecommerce  
2. react native mobile app 4+ years  
3. available healthcare nlp  
4. backend docker postgres  
5. computer vision retail  
6. azure databricks pyspark 5+  
7. frontend typescript next.js  
8. gcp bigquery dbt marketing analytics  

---

## Results Table

| # | Query                                | Baseline | Semantic | Hybrid | Verdict | Notes |
|---|--------------------------------------|----------|----------|--------|---------|-------|
| 1 | python aws 3+ years ecommerce        | ✓ good   | ✓ good   | ✓ best | Hybrid  | Hybrid surfaced both Python + AWS + ecommerce |
| 2 | react native mobile app 4+ years     | ✗ weak   | ✓ better | ✓ best | Hybrid  | Semantic caught RN alias; baseline missed |
| 3 | available healthcare nlp             | ✓ ok     | ✓ good   | ✓ good | Tie     | Availability respected |
| 4 | backend docker postgres              | ✓ good   | ✓ mid    | ✓ good | Baseline | Semantic less strong for infra keywords |
| 5 | computer vision retail               | ✗ weak   | ✓ good   | ✓ best | Hybrid  | Domain CV+Retail stronger semantically |
| 6 | azure databricks pyspark 5+          | ✗ weak   | ✓ better | ✓ best | Hybrid  | Semantic nailed cloud/data eng profile |
| 7 | frontend typescript next.js          | ✓ good   | ✓ good   | ✓ best | Hybrid  | Both worked, hybrid prioritized availability |
| 8 | gcp bigquery dbt marketing analytics | ✗ weak   | ✓ good   | ✓ good | Semantic | Semantic stronger at analytics domain |

---

## Improvements List
- Adjust hybrid weights (maybe semantic=0.7, keyword=0.3).  
- Add alias "rn" → "react native" (already noted).  
- Tune availability prioritization (sometimes semantic surfaced “soon” before “available”).  
- Extend normalization with more domain tokens: “infra”, “cv”, “analytics”.  

