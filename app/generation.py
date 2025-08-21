# app/generation.py
from __future__ import annotations
import os, json, uuid, time, logging
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from app.config import load_yaml, repo_path
from app.search.hybrid import hybrid_search

# ---------- Env & config ----------
load_dotenv()  # loads .env
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
GEN_CFG = load_yaml(repo_path("config", "generation.yaml"))

logger = logging.getLogger("hrbot.gen")

# ---------- Helpers ----------
def _summarize_request(query: str) -> str:
    # Simple one-liner. (You can improve later with your normalization pipeline.)
    return query.strip()

def _pick_candidates(hybrid_result: Dict[str, Any], k: int) -> List[Dict[str, Any]]:
    results = hybrid_result.get("results", [])
    return results[:k]

def _format_top_candidates_json(cands: List[Dict[str, Any]]) -> str:
    # Minimal metadata to keep it grounded—extend if you’d like.
    payload = []
    for r in cands:
        payload.append({
            "id": r.get("id"),
            "name": r.get("name"),
            "hybrid_score": r.get("hybrid_score"),
            "reason": r.get("reason_kw") or r.get("reason_sem") or "",
        })
    return json.dumps(payload, ensure_ascii=False, indent=2)

# ---------- Main ----------
def generate_response(query: str, top_k: Optional[int] = None, req_id: Optional[str] = None) -> Dict[str, Any]:
    """
    RAG generation:
      - hybrid retrieval
      - build grounded prompt
      - LLM call with timeout
      - on error/timeout -> graceful fallback using retrieved candidates
    """
    rid = req_id or str(uuid.uuid4())
    k = top_k or int(GEN_CFG.get("k", 3))

    # 1) Retrieve candidates via hybrid (fetch a few extra, then slice)
    t0 = time.perf_counter()
    hyb = hybrid_search(query, top_k=max(k, 10))
    t_hybrid_ms = (time.perf_counter() - t0) * 1000.0

    cands = _pick_candidates(hyb, k)

    # Edge case: no matches
    if not cands:
        text = (
            f"I couldn’t find strong matches for “{query}”. "
            "Want me to relax constraints (e.g., lower min years or include 'soon' availability)?"
        )
        logger.info(f"req_id={rid} phase=retrieve latency_ms={t_hybrid_ms:.1f} k={k} used=0 no_matches=1")
        return {"query": query, "used_candidate_ids": [], "response_text": text, "notes": {"no_matches": True, "k": k}}

    # 2) Build prompt from template/spec
    request_summary = _summarize_request(query)
    top_candidates_json = _format_top_candidates_json(cands)

    max_words = int(GEN_CFG.get("max_words", 200))
    next_steps_default = GEN_CFG.get("phrasing", {}).get(
        "next_steps_default",
        "Shall I widen skills or lower min years, or include 'soon' availability?"
    )

    system_msg = (
        "You are an assistant that recommends employees for internal projects. "
        "Ground every fact in the provided profiles. Do not invent facts. "
        "If uncertain or results are weak, ask a clarifying question."
    )
    user_msg = (
        f'Request: "{query}"\n\n'
        f"Top candidates (JSON):\n{top_candidates_json}\n\n"
        f"Constraints:\n"
        f"- Use only the fields present.\n"
        f"- Prefer availability=available, then soon, then unavailable.\n"
        f"- Keep total reply under {max_words} words.\n"
        f"- Suggest exactly {k} candidates when possible.\n\n"
        "Write the response in this format:\n"
        "1) One-line summary of the requirement.\n"
        "2) 2–3 candidate lines (name — why fit — availability).\n"
        "3) Next steps or a clarifying question if needed."
    )

    # 3) Call the model with timeout; on failure -> fallback
    client = OpenAI()
    try:
        t1 = time.perf_counter()
        resp = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.2,
            timeout=20,  # seconds (request-level timeout)
        )
        t_gen_ms = (time.perf_counter() - t1) * 1000.0

        text = resp.choices[0].message.content.strip() if resp.choices else "(no response)"
        logger.info(
            f"req_id={rid} phase=retrieve latency_ms={t_hybrid_ms:.1f} "
            f"phase=generate latency_ms={t_gen_ms:.1f} k={k} used={len(cands)}"
        )
        return {
            "query": query,
            "used_candidate_ids": [c.get("id") for c in cands],
            "response_text": text,
            "notes": {"k": k, "max_words": max_words},
        }

    except Exception as e:
        # 4) Graceful fallback: list retrieved candidates with short reasons
        logger.exception(f"req_id={rid} phase=generate error={type(e).__name__}")
        lines = ["Generation failed; showing retrieved candidates:"]
        for c in cands:
            name = c.get("name", "")
            meta = c.get("meta", {}) or {}
            avail = meta.get("availability", "n/a")
            why = c.get("reason_kw") or c.get("reason_sem") or ""
            lines.append(f"- {name} (availability: {avail}) — {why}")
        fallback_text = "\n".join(lines)

        return {
            "query": query,
            "used_candidate_ids": [c.get("id") for c in cands],
            "response_text": fallback_text,
            "notes": {"k": k, "fallback": True},
        }
