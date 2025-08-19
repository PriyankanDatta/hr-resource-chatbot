from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Any, Optional
import re
from pathlib import Path

from app.config import load_json, load_yaml, repo_path

# ---------- Load configs & data ----------

NORMALIZATION = load_json(repo_path("config", "normalization.json"))
BASELINE_CFG = load_yaml(repo_path("config", "baseline.yaml"))
EMPLOYEES = load_json(repo_path("data", "employees.json"))["employees"]

STOPWORDS: Set[str] = set(NORMALIZATION.get("stopwords", []))
PUNCT_TO_STRIP: List[str] = NORMALIZATION.get("punctuation_chars_to_strip", [])
SKILL_ALIASES: Dict[str, str] = NORMALIZATION.get("skill_aliases", {})
DOMAIN_ALIASES: Dict[str, str] = NORMALIZATION.get("domain_aliases", {})
AVAIL_ALIASES: Dict[str, str] = NORMALIZATION.get("availability_aliases", {})
EXP_PATTERNS: List[str] = NORMALIZATION.get("min_experience_patterns", [])

WEIGHTS = BASELINE_CFG.get("weights", {"skills": 3, "domains": 2, "projects": 1})
MIN_TOKEN_MATCH = int(BASELINE_CFG.get("min_token_match", 1))
TOP_K_DEFAULT = int(BASELINE_CFG.get("top_k", 5))

AVAIL_ORDER = {"available": 3, "soon": 2, "unavailable": 1}  # for tie-break

# Precompile experience regexes
EXP_REGEXES = [re.compile(p, flags=re.I) for p in EXP_PATTERNS]

def _strip_punct(s: str) -> str:
    if not PUNCT_TO_STRIP:
        return s
    tbl = str.maketrans({ch: " " for ch in PUNCT_TO_STRIP})
    return s.translate(tbl)

def _collapse_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def _alias_expand(token: str) -> str:
    # expand via skill or domain aliases; if multiple maps define it, skill wins
    if token in SKILL_ALIASES:
        return SKILL_ALIASES[token]
    if token in DOMAIN_ALIASES:
        return DOMAIN_ALIASES[token]
    return token

def normalize_to_tokens(text: str) -> List[str]:
    """Lowercase, strip punctuation, collapse spaces, split, alias-expand, remove stopwords."""
    t = text.lower()
    t = _strip_punct(t)
    t = _collapse_spaces(t)
    tokens = t.split() if t else []
    expanded = [_alias_expand(tok) for tok in tokens]
    return [tok for tok in expanded if tok and tok not in STOPWORDS]

def normalize_list_to_token_set(items: List[str]) -> Set[str]:
    """Normalize a list of phrases into a set of tokens."""
    toks: Set[str] = set()
    for item in items:
        for tok in normalize_to_tokens(item):
            toks.add(tok)
    return toks

def extract_min_experience(q_lower: str) -> Optional[int]:
    for rgx in EXP_REGEXES:
        m = rgx.search(q_lower)
        if m:
            try:
                return int(m.group(1))
            except Exception:
                continue
    return None

def extract_availability(q_lower: str) -> Optional[str]:
    # Look for exact words or known alias phrases inside the query
    for phrase, mapped in AVAIL_ALIASES.items():
        if phrase in q_lower:
            return mapped
    for bucket in ("available", "soon", "unavailable"):
        if bucket in q_lower:
            return bucket
    return None

# ---------- Prepare employee candidate bags ----------

@dataclass(frozen=True)
class CandidateBag:
    id: int
    name: str
    experience_years: int
    availability: str
    skills: Set[str]
    projects: Set[str]
    domains: Set[str]

def build_candidate_bag(emp: Dict[str, Any]) -> CandidateBag:
    return CandidateBag(
        id=int(emp["id"]),
        name=emp.get("name", ""),
        experience_years=int(emp.get("experience_years", 0)),
        availability=str(emp.get("availability", "")).lower(),
        skills=normalize_list_to_token_set(emp.get("skills", [])),
        projects=normalize_list_to_token_set(emp.get("projects", [])),
        domains=normalize_list_to_token_set(emp.get("domains", [])),
    )

CANDIDATES: List[CandidateBag] = [build_candidate_bag(e) for e in EMPLOYEES]

# ---------- Core baseline search ----------

@dataclass
class SearchFilters:
    min_experience_years: Optional[int]
    availability: Optional[str]

@dataclass
class MatchResult:
    id: int
    name: str
    score: int
    matched_terms: Dict[str, List[str]]
    experience_years: int
    availability: str

def parse_filters(original_query: str) -> SearchFilters:
    q_lower = original_query.lower()
    min_years = extract_min_experience(q_lower)
    availability = extract_availability(q_lower)
    return SearchFilters(min_experience_years=min_years, availability=availability)

def apply_filters(cands: List[CandidateBag], flt: SearchFilters) -> List[CandidateBag]:
    out = []
    for c in cands:
        if flt.min_experience_years is not None and c.experience_years < flt.min_experience_years:
            continue
        if flt.availability is not None and c.availability != flt.availability:
            continue
        out.append(c)
    return out

def score_candidate(query_tokens: Set[str], c: CandidateBag) -> Tuple[int, Dict[str, List[str]]]:
    skill_hits = sorted(list(query_tokens.intersection(c.skills)))
    domain_hits = sorted(list(query_tokens.intersection(c.domains)))
    project_hits = sorted(list(query_tokens.intersection(c.projects)))

    num_skill = len(skill_hits)
    num_domain = len(domain_hits)
    num_project = len(project_hits)

    total_matches = num_skill + num_domain + num_project
    if total_matches < MIN_TOKEN_MATCH:
        return 0, {"skills": [], "domains": [], "projects": []}

    score = (WEIGHTS.get("skills", 3) * num_skill
            + WEIGHTS.get("domains", 2) * num_domain
            + WEIGHTS.get("projects", 1) * num_project)

    matched_terms = {
        "skills": skill_hits,
        "domains": domain_hits,
        "projects": project_hits
    }
    return score, matched_terms

def availability_rank(avail: str) -> int:
    return AVAIL_ORDER.get(avail, 0)

def baseline_search(query: str, top_k: Optional[int] = None) -> Dict[str, Any]:
    # Extract filters from the raw query, then normalize into tokens
    filters = parse_filters(query)
    query_tokens = set(normalize_to_tokens(query))

    # Filter candidates first
    survivors = apply_filters(CANDIDATES, filters)

    # Score the survivors
    results: List[MatchResult] = []
    for c in survivors:
        score, matched_terms = score_candidate(query_tokens, c)
        if score > 0:
            results.append(MatchResult(
                id=c.id, name=c.name, score=score, matched_terms=matched_terms,
                experience_years=c.experience_years, availability=c.availability
            ))

    # Sort: score desc, experience desc, availability (available>soon>unavailable), id asc
    results.sort(key=lambda r: (-r.score, -r.experience_years, -availability_rank(r.availability), r.id))

    k = top_k or TOP_K_DEFAULT
    top = results[:k]

    # Build response with reasons
    resp_results = []
    for r in top:
        parts = []
        if r.matched_terms["skills"]:
            parts.append(f"skills: {', '.join(r.matched_terms['skills'])}")
        if r.matched_terms["domains"]:
            parts.append(f"domains: {', '.join(r.matched_terms['domains'])}")
        if r.matched_terms["projects"]:
            parts.append(f"projects: {', '.join(r.matched_terms['projects'])}")
        detail = "; ".join(parts) if parts else "partial match"

        reason = f"Matched {detail}; experience={r.experience_years}y; availability={r.availability}."
        resp_results.append({
            "id": r.id,
            "name": r.name,
            "score": r.score,
            "matched_terms": r.matched_terms,
            "reason": reason
        })

    return {
        "query": query,
        "filters_applied": {
            "min_experience_years": filters.min_experience_years,
            "availability": filters.availability
        },
        "top_k": k,
        "results": resp_results
    }
