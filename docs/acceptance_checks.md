# Acceptance Checks (v1)

## For each intent

### 1) Skill match
- At least one candidate where `skills` contains all requested skills (after alias normalization).
- If none, return "closest matches" with explanation of partial overlap.

### 2) Experience threshold
- Top results satisfy `experience_years >= min_experience_years`.
- If not enough results, show those within 1 year of the threshold, labeled "near match".

### 3) Domain experience
- At least one candidate where `domains` contains requested domain(s) after alias normalization.

### 4) Availability
- If availability is specified, first page shows ONLY profiles with that availability.
- If zero results, the system explicitly says "No candidates currently 'available'. Here are 'soon' options."

### 5) Role suggestion
- Response lists 2–3 candidates.
- Each candidate includes a "why matched" line referencing skills AND domain and/or experience_years.

## Global checks
- Latency (local) <= 3s; (deployed) <= 5s.
- No hallucinated fields: all facts come from `employees.json`.
- If <2 good matches: return a clarifying question suggestion (e.g., add skill, domain, or min years).
