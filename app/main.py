from fastapi import FastAPI, Query, Body
from typing import Optional

from app.search.baseline import baseline_search
from app.search.semantic import semantic_search
from app.search.hybrid import hybrid_search
from app.generation import generate_response  # NEW

app = FastAPI(title="HR Resource Chatbot API", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "Hello from FastAPI — backend is running!"}

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
