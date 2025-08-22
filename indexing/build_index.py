# indexing/build_index.py
from __future__ import annotations
import os, json, time
from pathlib import Path
from typing import List, Dict, Any
import re
import numpy as np

from dotenv import load_dotenv
from openai import OpenAI
import faiss  # type: ignore

# ---------- Paths ----------
ROOT = Path(__file__).resolve().parents[1]   # repo root
DATA_DIR = ROOT / "data"
CONFIG_DIR = ROOT / "config"

EMP_PATH = DATA_DIR / "employees.json"
NORM_PATH = CONFIG_DIR / "normalization.json"

INDEX_OUT = DATA_DIR / "employee_index.faiss"
META_OUT  = DATA_DIR / "employee_meta.json"
STATS_OUT = DATA_DIR / "employee_index.stats.json"

# ---------- Load env & configs ----------
load_dotenv()  # loads .env (kept out of git)
EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")

with NORM_PATH.open("r", encoding="utf-8") as f:
    NORM = json.load(f)

STOPWORDS = set(NORM.get("stopwords", []))
PUNCT = NORM.get("punctuation_chars_to_strip", [])
SKILL_ALIASES = NORM.get("skill_aliases", {})
DOMAIN_ALIASES = NORM.get("domain_aliases", {})

def strip_punct(s: str) -> str:
    if not PUNCT:
        return s
    tbl = str.maketrans({ch: " " for ch in PUNCT})
    return s.translate(tbl)

def collapse_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def alias_expand(tok: str) -> str:
    if tok in SKILL_ALIASES: return SKILL_ALIASES[tok]
    if tok in DOMAIN_ALIASES: return DOMAIN_ALIASES[tok]
    return tok

def normalize_text(s: str) -> str:
    s = s.lower()
    s = strip_punct(s)
    s = collapse_spaces(s)
    toks = [alias_expand(t) for t in (s.split() if s else [])]
    toks = [t for t in toks if t and t not in STOPWORDS]
    return " ".join(toks)

# ---------- Load employees ----------
with EMP_PATH.open("r", encoding="utf-8") as f:
    employees = json.load(f)["employees"]

def profile_blob(emp: Dict[str, Any]) -> str:
    # Build a single, normalized text blob per employee
    name = emp.get("name", "")
    skills = ", ".join(emp.get("skills", []))
    projects = ", ".join(emp.get("projects", []))
    domains = ", ".join(emp.get("domains", []))
    exp = f"{emp.get('experience_years', 0)} years experience"
    avail = f"availability {emp.get('availability','')}"
    raw = f"{name}. skills: {skills}. projects: {projects}. domains: {domains}. {exp}. {avail}."
    return normalize_text(raw)

texts: List[str] = [profile_blob(e) for e in employees]

# ---------- Embed ----------
client = OpenAI()
print(f"Embedding {len(texts)} profiles with model: {EMBED_MODEL} ...")
resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
vecs = np.array([d.embedding for d in resp.data], dtype="float32")

# L2-normalize so inner product ≈ cosine similarity
faiss.normalize_L2(vecs)

# ---------- Build FAISS index ----------
d = vecs.shape[1]
index = faiss.IndexFlatIP(d)
index.add(vecs)
assert index.ntotal == len(texts)

# ---------- Save artifacts ----------
print(f"Saving index → {INDEX_OUT}")
faiss.write_index(index, str(INDEX_OUT))

meta = []
for row_id, emp in enumerate(employees):
    meta.append({
        "row_id": row_id,
        "employee_id": emp["id"],
        "name": emp.get("name",""),
        "top_fields": {
            "skills": emp.get("skills", [])[:6],
            "domains": emp.get("domains", [])[:6],
            "availability": emp.get("availability",""),
            "experience_years": emp.get("experience_years",0)
        }
    })

with META_OUT.open("w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

stats = {
    "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "model": EMBED_MODEL,
    "embedding_dim": int(d),
    "num_items": int(index.ntotal),
    "faiss_index": "IndexFlatIP",
}
with STATS_OUT.open("w", encoding="utf-8") as f:
    json.dump(stats, f, ensure_ascii=False, indent=2)

print("Done.")
print(json.dumps(stats, indent=2))
