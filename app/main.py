from fastapi import FastAPI, Query, Body, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from app.search.baseline import baseline_search
from app.search.semantic import semantic_search
from app.search.hybrid import hybrid_search
from app.generation import generate_response

app = FastAPI(title="HR Resource Chatbot API", version="0.1.0")

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

# ===== Existing Search Endpoints =====
@app.get("/search/keyword")
def search_keyword(
    q: str = Query(..., description="User query, e.g. 'python aws 3+ years ecommerce'"),
    top_k: Optional[int] = Query(None, ge=1, le=50),
):
    """
    Baseline keyword search over employees.json using normalization, filters, and scoring per docs/baseline_search.md.
    """
    return baseline_search(q, top_k=top_k)

@app.get("/search/semantic")
def search_semantic(
    q: str = Query(..., description="User query for semantic search"),
    top_k: Optional[int] = Query(None, ge=1, le=50),
):
    """
    Semantic search over FAISS index built in Step 9.2.
    """
    return semantic_search(q, top_k=top_k)

@app.get("/search/hybrid")
def search_hybrid_endpoint(
    q: str = Query(..., description="User query for hybrid (semantic + keyword) search"),
    top_k: Optional[int] = Query(None, ge=1, le=50),
):
    """
    Hybrid search: combines semantic similarity (FAISS) and keyword score per config/semantic.yaml (hybrid_weights).
    """
    return hybrid_search(q, top_k=top_k)

# ===== Generation Endpoint (implementation of Step 10) =====
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

# ===== Contract Aliases (Step 12) =====
@app.post("/chat", response_model=ChatResponse, tags=["contract"])
def chat(body: ChatRequest):
    """
    Contract alias for generation. POST /chat with:
    { "query": "python aws 3+ years ecommerce available", "top_k": 3 }
    """
    out = generate_response(body.query, top_k=body.top_k)
    return ChatResponse(
        response_text=out["response_text"],
        used_candidate_ids=out["used_candidate_ids"],
    )

@app.get("/employees/search", response_model=EmployeeSearchResponse, tags=["contract"])
def employees_search(
    skill: Optional[str] = Query(None, description="Single skill to match (exact/alias-normalized)"),
    min_experience: Optional[int] = Query(None, ge=0, description="Minimum years of experience"),
    domain: Optional[str] = Query(None, description="Single domain tag, e.g., ecommerce"),
    availability: Optional[str] = Query(None, regex="^(available|soon|unavailable)$",
                                        description="Availability bucket"),
    top_k: Optional[int] = Query(5, ge=1, le=50),
):
    """
    Param-based wrapper over baseline search.
    Build a simple query string from provided params and reuse baseline_search.
    """
    if not any([skill, min_experience, domain, availability]):
        raise HTTPException(status_code=400,
                            detail="Provide at least one of: skill, min_experience, domain, availability")

    parts = []
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
        items.append(CandidateOut(
            id=r["id"],
            name=r["name"],
            why=r.get("reason"),
        ))
    return EmployeeSearchResponse(results=items)
