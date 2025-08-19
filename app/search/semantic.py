# app/search/semantic.py
from __future__ import annotations
import os, json, re
from typing import Any, Dict, List, Optional

import numpy as np
import faiss  # type: ignore
from dotenv import load_dotenv
from openai import OpenAI

# ✅ use the shared helpers from app/config.py
from app.config import repo_path, load_json, load_yaml

# ---------- Load env & configs ----------
load_dotenv()  # reads local .env (not committed)
SEM_CFG = load_yaml(repo_path("config", "semantic.yaml"))
NORM = load_json(repo_path("config", "normalization.json"))

EMBED_MODEL = os.getenv("EMBEDDING_MODEL", SEM_CFG.get("model", "text-embedding-3-large"))
TOP_K_DEFAULT = int(SEM_CFG.get("top_k", 5))

OUTS = SEM_CFG.get("outputs", {})
INDEX_PATH = repo_path(OUTS.get("faiss", "data/employee_index.faiss"))
META_PATH  = repo_path(OUTS.get("meta",  "data/employee_meta.json"))

# ---------- Normalization (mirror indexer behavior) ----------
STOPWORDS = set(NORM.get("stopwords", []))
PUNCT = NORM.get("punctuation_chars_to_strip", [])
SKILL_ALIASES = NORM.get("skill_aliases", {})
DOMAIN_ALIASES = NORM.get("domain_aliases", {})

def _strip_punct(s: str) -> str:
    if not PUNCT:
        return s
    tbl = str.maketrans({ch: " " for ch in PUNCT})
    return s.translate(tbl)

def _collapse_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def _alias_expand(tok: str) -> str:
    if tok in SKILL_ALIASES:  return SKILL_ALIASES[tok]
    if tok in DOMAIN_ALIASES: return DOMAIN_ALIASES[tok]
    return tok

def normalize_text(s: str) -> str:
    s = s.lower()
    s = _strip_punct(s)
    s = _collapse_spaces(s)
    toks = [ _alias_expand(t) for t in (s.split() if s else []) ]
    toks = [ t for t in toks if t and t not in STOPWORDS ]
    return " ".join(toks)

# ---------- Load FAISS + meta once ----------
_index: Optional[faiss.Index] = None
_meta: Optional[List[Dict[str, Any]]] = None
_dim: Optional[int] = None
_client: Optional[OpenAI] = None

def _ensure_loaded():
    global _index, _meta, _dim, _client
    if _index is None:
        if not INDEX_PATH.exists():
            raise FileNotFoundError(f"FAISS index not found at {INDEX_PATH}")
        _index = faiss.read_index(str(INDEX_PATH))
        _dim = _index.d
    if _meta is None:
        if not META_PATH.exists():
            raise FileNotFoundError(f"Meta file not found at {META_PATH}")
        _meta = load_json(META_PATH)
    if _client is None:
        _client = OpenAI()

def _embed_query(text: str) -> np.ndarray:
    """Embed and L2-normalize a single query string."""
    assert _client is not None
    resp = _client.embeddings.create(model=EMBED_MODEL, input=[text])
    v = np.array(resp.data[0].embedding, dtype="float32")
    faiss.normalize_L2(v.reshape(1, -1))
    return v

def semantic_search(query: str, top_k: Optional[int] = None) -> Dict[str, Any]:
    """
    Normalize query -> embed -> FAISS search -> hydrate meta.
    Returns: { query, top_k, results: [{id,name,sem_score,meta}] }
    """
    _ensure_loaded()
    assert _index is not None and _meta is not None

    q_norm = normalize_text(query)
    vec = _embed_query(q_norm)

    k = top_k or TOP_K_DEFAULT
    D, I = _index.search(vec.reshape(1, -1), k)  # inner-product scores
    scores = D[0].tolist()
    idxs = I[0].tolist()

    results = []
    for row_id, score in zip(idxs, scores):
        if row_id < 0:  # FAISS returns -1 if fewer than k items
            continue
        m = _meta[row_id]
        results.append({
            "id": m["employee_id"],
            "name": m.get("name", ""),
            "sem_score": float(score),
            "meta": m["top_fields"]
        })

    return {
        "query": query,
        "normalized_query": q_norm,
        "top_k": k,
        "results": results
    }
