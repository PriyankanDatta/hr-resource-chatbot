from fastapi import FastAPI, Query, Body, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid, time, logging, re  # logging + re for guard

from app.search.baseline import baseline_search
from app.search.semantic import semantic_search
from app.search.hybrid import hybrid_search
from app.generation import generate_response

from functools import lru_cache
from app.config import repo_path, load_json

from fastapi.middleware.cors import CORSMiddleware



# Logger for API observability
logger = logging.getLogger("hrbot.api")

app = FastAPI(title="HR Resource Chatbot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # for hackathon; lock down later if you want
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Contract Models (for nicer OpenAPI + validation) =====
class ChatRequest(BaseModel):
    query: str = Field(min_length=3, description="User request text")
    top_k: Optional[int] = Field(default=3, ge=1, le=20)

class CandidateOut(BaseModel):
    id: int
    name: str
    why: Optional[str] = None

class ChatResponse(BaseModel):
    response_text: str
    used_candidate_ids: List[int]

class EmployeeSearchResponse(BaseModel):
    results: List[CandidateOut]

# ===== Health & Root =====
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "Hello from FastAPI — backend is running!"}


# ===== Facets (skills/domains) =====
def _norm_token(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s

@lru_cache(maxsize=1)
def _load_facets_cached():
    # Load data + normalization rules
    employees = load_json(repo_path("data", "employees.json")).get("employees", [])
    norm = load_json(repo_path("config", "normalization.json"))
    skill_aliases = { _norm_token(k): _norm_token(v) for k, v in norm.get("skill_aliases", {}).items() }
    domain_aliases = { _norm_token(k): _norm_token(v) for k, v in norm.get("domain_aliases", {}).items() }

    skills_set = set()
    domains_set = set()

    def canon_skill(tok: str) -> str:
        t = _norm_token(tok)
        return skill_aliases.get(t, t)

    def canon_domain(tok: str) -> str:
        t = _norm_token(tok)
        return domain_aliases.get(t, t)

    for emp in employees:
        for sk in emp.get("skills", []) or []:
            skills_set.add(canon_skill(sk))
        for dm in emp.get("domains", []) or []:
            domains_set.add(canon_domain(dm))

    skills = sorted([s for s in skills_set if s])
    domains = sorted([d for d in domains_set if d])

    return {
        "skills": skills,
        "domains": domains,
        "availability": ["available", "soon", "unavailable"],
        "counts": {
            "skills": len(skills),
            "domains": len(domains),
            "employees": len(employees)
        }
    }

@app.get("/metadata/facets", tags=["metadata"])
def get_facets():
    """
    Returns canonical lists of skills and domains for dropdowns, plus availability buckets.
    Uses normalization/alias rules from config/normalization.json.
    """
    return _load_facets_cached()


# ===== Search Endpoints =====
@app.get("/search/keyword")
def search_keyword(
    q: str = Query(..., description="User query, e.g. 'python aws 3+ years ecommerce'"),
    top_k: Optional[int] = Query(None, ge=1, le=50),
):
    """
    Baseline keyword search over employees.json using normalization, filters, and scoring.
    See docs/baseline_search.md.
    """
    return baseline_search(q, top_k=top_k)

@app.get("/search/semantic")
def search_semantic(
    q: str = Query(..., description="User query for semantic search"),
    top_k: Optional[int] = Query(None, ge=1, le=50),
):
    """Semantic search over FAISS index built in Step 9.2."""
    return semantic_search(q, top_k=top_k)

@app.get("/search/hybrid")
def search_hybrid_endpoint(
    q: str = Query(..., description="User query for hybrid (semantic + keyword) search"),
    top_k: Optional[int] = Query(None, ge=1, le=50),
):
    """Hybrid search: combines semantic similarity and keyword score per config/semantic.yaml (hybrid_weights)."""
    return hybrid_search(q, top_k=top_k)

# ===== Generation Endpoint (Step 10 implementation) =====
@app.post("/generate")
def generate(
    q: str = Body(..., embed=True, description="User request text, e.g., 'python aws 3+ years ecommerce available'"),
    top_k: Optional[int] = Body(None, embed=True),
):
    """
    RAG generation endpoint:
    - Calls hybrid retrieval
    - Builds a grounded prompt (docs/prompt_template_generation.md)
    - Calls CHAT_MODEL from .env
    - Returns concise, grounded recommendation text
    """
    return generate_response(q, top_k=top_k)

# ===== Contract Alias: POST /chat =====
@app.post("/chat", response_model=ChatResponse, tags=["contract"])
def chat(body: ChatRequest):
    """
    Contract alias for generation. POST /chat with:
    { "query": "python aws 3+ years ecommerce available", "top_k": 3 }
    """
    # ---- Absurd threshold guard for /chat as well ----
    m = re.search(r"(\d+)\s*\+?\s*(?:years|yrs|yr)", body.query, flags=re.I)
    if m:
        yrs = int(m.group(1))
        if yrs > 50:
            raise HTTPException(status_code=400, detail="min_experience is unrealistic (>50)")

    # ---- Request ID + timing + logging ----
    req_id = str(uuid.uuid4())
    t0 = time.perf_counter()
    try:
        out = generate_response(body.query, top_k=body.top_k, req_id=req_id)
        dt_ms = (time.perf_counter() - t0) * 1000.0
        logger.info(
            f"req_id={req_id} route=/chat latency_ms={dt_ms:.1f} "
            f"k={body.top_k} used={len(out.get('used_candidate_ids', []))}"
        )
        return ChatResponse(
            response_text=out["response_text"],
            used_candidate_ids=out["used_candidate_ids"],
        )
    except Exception as e:
        dt_ms = (time.perf_counter() - t0) * 1000.0
        logger.exception(f"req_id={req_id} route=/chat error={type(e).__name__} latency_ms={dt_ms:.1f}")
        raise

# ===== Param-based wrapper over baseline =====
@app.get("/employees/search", response_model=EmployeeSearchResponse, tags=["contract"])
def employees_search(
    skill: Optional[str] = Query(None, description="Single skill to match (exact/alias-normalized)"),
    min_experience: Optional[int] = Query(None, ge=0, description="Minimum years of experience"),
    domain: Optional[str] = Query(None, description="Single domain tag, e.g., ecommerce"),
    availability: Optional[str] = Query(
        None,
        regex="^(available|soon|unavailable)$",
        description="Availability bucket",
    ),
    top_k: Optional[int] = Query(5, ge=1, le=50),
):
    """Build a simple query string from provided params and reuse baseline_search."""
    # Absurd threshold validation
    if min_experience is not None and min_experience > 50:
        raise HTTPException(status_code=400, detail="min_experience is unrealistic (>50)")

    if not any([skill, min_experience, domain, availability]):
        raise HTTPException(
            status_code=400,
            detail="Provide at least one of: skill, min_experience, domain, availability",
        )

    parts: List[str] = []
    if skill:
        parts.append(skill)
    if min_experience is not None:
        parts.append(f"{min_experience}+ years")
    if domain:
        parts.append(domain)
    if availability:
        parts.append(availability)
    q = " ".join(parts)

    res = baseline_search(q, top_k=top_k)
    items: List[CandidateOut] = []
    for r in res.get("results", []):
        items.append(
            CandidateOut(
                id=r["id"],
                name=r["name"],
                why=r.get("reason"),
            )
        )
    return EmployeeSearchResponse(results=items)
