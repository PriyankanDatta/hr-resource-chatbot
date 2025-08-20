# app/search/hybrid.py
from __future__ import annotations
from typing import Any, Dict, List, Optional
import numpy as np

from app.search.baseline import baseline_search
from app.search.semantic import semantic_search
from app.config import repo_path, load_yaml

# Load hybrid weights from semantic.yaml
SEM_CFG = load_yaml(repo_path("config", "semantic.yaml"))
W = SEM_CFG.get("hybrid_weights", {"semantic": 0.6, "keyword": 0.4})

def _normalize_scores(results: List[Dict[str, Any]], field: str) -> None:
    """Normalize scores in-place to 0..1 for fair combination."""
    scores = [r[field] for r in results if r.get(field) is not None]
    if not scores:
        return
    min_s, max_s = min(scores), max(scores)
    rng = max_s - min_s if max_s > min_s else 1.0
    for r in results:
        if r.get(field) is not None:
            r[field + "_norm"] = (r[field] - min_s) / rng
        else:
            r[field + "_norm"] = 0.0

def hybrid_search(query: str, top_k: Optional[int] = None) -> Dict[str, Any]:
    # Run both searches
    kw = baseline_search(query, top_k)
    sem = semantic_search(query, top_k)

    # Index results by id
    merged: Dict[int, Dict[str, Any]] = {}
    for r in kw["results"]:
        merged[r["id"]] = {
            "id": r["id"],
            "name": r["name"],
            "kw_score": r["score"],
            "reason_kw": r["reason"],
        }
    for r in sem["results"]:
        if r["id"] not in merged:
            merged[r["id"]] = {"id": r["id"], "name": r["name"]}
        merged[r["id"]]["sem_score"] = r["sem_score"]
        merged[r["id"]]["reason_sem"] = f"Semantic match on {', '.join(r['meta'])}"

    # Convert to list
    results = list(merged.values())

    # Normalize scores
    _normalize_scores(results, "kw_score")
    _normalize_scores(results, "sem_score")

    # Combine
    for r in results:
        r["hybrid_score"] = (
            W["semantic"] * r.get("sem_score_norm", 0.0) +
            W["keyword"]  * r.get("kw_score_norm", 0.0)
        )

    # Sort by hybrid score desc
    results = sorted(results, key=lambda r: r["hybrid_score"], reverse=True)

    # Truncate
    if top_k:
        results = results[:top_k]

    return {
        "query": query,
        "top_k": top_k,
        "weights": W,
        "results": results
    }
