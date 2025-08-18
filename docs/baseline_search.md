# Baseline Keyword Search (v1)

## Purpose
Deterministic, simple search over `data/employees.json` using normalized keywords as a fallback and as a baseline to compare with semantic search.

## Inputs
- Raw user query string (e.g., "python aws 3+ years ecommerce available").

## Normalization
Use `config/normalization.json`:
- lowercase
- strip punctuation
- collapse spaces
- expand aliases (e.g., "ml" → "machine learning", "reactnative" → "react native")
- remove stopwords (light list)

## Fields to Search
- `skills` (list of strings)
- `projects` (list of short strings)
- `domains` (list of strings)

## Candidate Text per Employee
For each employee, build a normalized candidate bag:
candidate.skills := normalized(skills[])
candidate.projects := normalized(projects[])
candidate.domains := normalized(domains[])

## Matching Rule (Token Overlap Count)
1) Normalize the user query using the same rules → **query tokens**  
2) For each employee:
   - Count how many query tokens appear in **skills**, **projects**, **domains**
   - Track which tokens matched in which field → `matched_terms`

## Scoring (field weights)
Configured in `config/baseline.yaml`:
- skills: **3**
- domains: **2**
- projects: **1**

Final keyword score:
score = (3 * #skill_matches) + (2 * #domain_matches) + (1 * #project_matches)

Discard profiles where **total matches < `min_token_match`** (default: 1).

## Result Shape
Return **top_k** items by keyword score (ties handled in Step 8.2):

```json
[
  {
    "id": 123,
    "name": "Full Name",
    "score": 7,
    "matched_terms": {
      "skills": ["python", "aws"],
      "domains": ["ecommerce"],
      "projects": ["pricing service"]
    },
    "reason": "Matched skills: python, aws; domains: ecommerce; experience=5y; availability=available"
  }
]

## Filters (Step 8.2)

**min_experience_years**  
- Keep profiles where `experience_years >= requested_min`.  
- If no min specified, keep all.  

**availability**  
- If specified, keep only profiles with that `availability` bucket (`available`, `soon`, `unavailable`).  
- If not specified, keep all.  

👉 Apply these filters **before** computing keyword scores.  

## Tie-Breaker Rules

If multiple profiles have the same score:  
1. Prefer **higher `experience_years`**.  
2. Then prefer availability in this order: `available` > `soon` > `unavailable`.  
3. Finally, prefer lower `id` (stable ordering).


## Return Format (Step 8.3)

After filtering (8.2) and scoring (8.1), return the **top_k** results with clear reasons.

**Default:** `top_k` from `config/baseline.yaml` (e.g., 5).

### Per-result fields
- `id`, `name`
- `score` — keyword score only (weighted token overlap)
- `matched_terms` — which tokens matched in which field
  - `skills`: []
  - `domains`: []
  - `projects`: []
- `reason` — one sentence explaining *why* this candidate matched

### Example response
```json
{
  "query": "python aws 3+ years ecommerce",
  "filters_applied": {
    "min_experience_years": 3,
    "availability": null
  },
  "top_k": 5,
  "results": [
    {
      "id": 1,
      "name": "Alice Johnson",
      "score": 8,
      "matched_terms": {
        "skills": ["python", "aws"],
        "domains": ["ecommerce"],
        "projects": []
      },
      "reason": "Matched skills: python, aws; domain: ecommerce; experience=5y; availability=available."
    },
    {
      "id": 7,
      "name": "Grace Lee",
      "score": 5,
      "matched_terms": {
        "skills": ["python"],
        "domains": [],
        "projects": []
      },
      "reason": "Matched skill: python; experience=6y; availability=available."
    }
  ]
}
