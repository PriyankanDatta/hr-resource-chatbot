# Retrieval Intents (v1)

## Intents we will support in v1
1. **Skill match** – “Find Python + SQL profiles”
2. **Experience threshold** – “3+ years React Native”
3. **Domain experience** – “Has healthcare projects”
4. **Availability** – “Who is available/soon?”
5. **Role suggestion** – “Suggest people for a backend project with Docker + AWS”

## Out of scope for v1 (explicit)
- Rate cards / cost
- PTO calendars
- Real HRIS fields (pulling live HR data)
- Location-based legal constraints


---

## Supported filters (v1)

- skills (exact/alias-normalized string match)  
- min_experience_years (≥ integer)  
- domains (alias-normalized)  
- availability ∈ {"available","soon","unavailable"}  

## Not supported (v1)

- location radius  
- certifications filtering  
- project recency  

