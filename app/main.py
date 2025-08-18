from fastapi import FastAPI, Query
from typing import Optional
from app.search.baseline import baseline_search

app = FastAPI(title="HR Resource Chatbot API", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "Hello from FastAPI — backend is running!"}

@app.get("/search/keyword")
def search_keyword(q: str = Query(..., description="User query, e.g. 'python aws 3+ years ecommerce'"),
                   top_k: Optional[int] = Query(None, ge=1, le=50)):
    """
    Baseline keyword search over employees.json using normalization, filters, and scoring per docs/baseline_search.md.
    """
    return baseline_search(q, top_k=top_k)
