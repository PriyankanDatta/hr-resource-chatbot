# Error Handling & Observability (v1)

## 14.1 Validation
- Empty query → 422 from /chat (min_length=3 already enforced).
- Absurd thresholds: min_experience > 50 → 400.
- Unknown availability → 400 (already validated by regex).
- Unknown skills: allow, but return “no strong matches” guidance.

## 14.2 Timeouts & Fallbacks
- Generation timeout 20s. On timeout or error:
  - Show "retrieved list" fallback (top-k hybrid) with a short template summary.
  - UI should label: “Generation failed; showing retrieved candidates.”

## 14.3 Logging
- Per request: request_id (uuid4), phase timings (baseline, semantic, hybrid, generate), candidate_count, http_status.
- Error logs include exception type and message only (no sensitive content).

## 14.4 Redaction
- Never log API keys or prompt contents.
- Dataset is synthetic; no PII. Re-affirm in README.
