# RAG Response Layer (v1)

## 10.1 Response Template (short)
Structure:
1) One-line summary of the requirement (echo back normalized intent)
2) 2–3 candidate suggestions (name → why fit → availability)
3) Next actions / clarifying question (if needed)

### Template (concise)
**Request summary:** {request_summary}

**Suggested candidates (k={k}):**
1) {c1.name} — why: {c1.why}. availability: {c1.availability}
2) {c2.name} — why: {c2.why}. availability: {c2.availability}
3) {c3.name} — why: {c3.why}. availability: {c3.availability}

**Next steps:** {next_steps}

---

## 10.2 Grounding Rules
- Only recommend from **retrieved profiles** (IDs returned by search).
- All *facts* must come **verbatim** from `employees.json` (skills, domains, years, availability).
- “Why fit” must explicitly cite at least one **skill** and one **domain** (if present).
- If a fact is missing, say “not specified” rather than inventing it.

## 10.3 Hallucination Guardrails
- If there are < 2 strong matches or key info is missing, **add a clarifying question**.
- Never fabricate certifications, locations, or experience years.
- Use phrases like: “Based on the retrieved profiles…” and “If you’d like, I can expand the search to …”.

## 10.4 Length & k
- `k = 3` default (configurable).
- Hard cap total response length ≈ **150–220 words**.
- Each candidate line ≤ **28–32 words**.

## 10.5 Edge Cases
- **No matches:** “No exact matches for X. Option A: relax min years; Option B: remove availability filter. Want me to try that?”
- **Too many matches:** “Found many profiles. I’m showing the top {k}. Want me to narrow by domain or raise min years?”
- **Conflicting constraints:** “You asked for `availability=available` and `React Native 8+ years`; none match. Try 5+ years or include ‘soon’?”
- **Near matches only:** Label as “near match” if within 1 year of min experience or missing 1 requested skill.

## Input → Output Mapping (contract)
- **Inputs:** `user_query`, `normalized_query`, `top_k_candidates` (each has id, name, skills, domains, years, availability, keyword/semantic scores)
- **Outputs:** `response_text`, `used_candidate_ids`, `notes` (clarifications asked? constraints relaxed?)
