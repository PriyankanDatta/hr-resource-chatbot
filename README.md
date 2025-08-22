# HR Resource Query Chatbot

## Overview
For HRs to query candidates.

## Features
- Keyword search (baseline)
- Semantic search with embeddings (FAISS)
- Hybrid retrieval
- RAG generation with guardrails
- Streamlit UI

## Architecture
Overview of system components.

## Setup & Installation
(Conda env, pip install -r requirements.txt, run_api.bat, run_ui.bat.)

## API Documentation
(Link to FastAPI auto-docs: `http://127.0.0.1:8000/docs`.)

## AI Development Process
How AI tools were used in development.

## Technical Decisions
Why certain tools/libraries were chosen.
**Backend:** FastAPI  
- Chosen for its simplicity, async capabilities, and built-in API docs.
- Trade-off: Requires Python env setup, but minimal compared to heavier frameworks.

**Frontend:** Streamlit  
- Chosen for rapid prototyping during hackathon.
- Trade-off: Less customizable styling compared to React.

**Embeddings & Vector Store:** FAISS (local)  
- Chosen for simplicity and no external hosting requirements.
- Trade-off: Not scalable for millions of records, but perfect for small synthetic dataset.

**LLM Path:** OpenAI API (Online)  
- Chosen for fast integration and reliable performance.
- Trade-off: Requires internet and small usage costs; local fallback would be Ollama.


## Future Improvements
Ideas for further work.


## 🎬 Demo

- **Live UI (Streamlit):** https://hr-resource-chatbot-6wgej3yfcpqe96icmpmxrp.streamlit.app/
- **API (Render):** https://hr-resource-chatbot-42wb.onrender.com
- **Docs (OpenAPI):** https://hr-resource-chatbot-42wb.onrender.com/docs

### Run locally
```bash
# Terminal A: API
scripts\run_api.bat

# Terminal B: UI (local)
scripts\run_ui.bat

## Evaluation

We maintain a small evaluation plan and gold query set to track performance of the search and generation system.

- [Evaluation Plan](tests/eval_plan.md): metrics, latency, and logging format  
- [Gold Queries](tests/gold_queries.json): 10–15 representative test queries for skills, domains, experience, and availability
