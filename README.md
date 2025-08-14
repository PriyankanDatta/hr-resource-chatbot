# HR Resource Query Chatbot

## Overview
Brief description of the project and its goal.

## Features
- Feature 1
- Feature 2

## Architecture
Overview of system components.

## Setup & Installation
Steps to run the project locally.

## API Documentation
Endpoint descriptions and examples.

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

## Demo
Link to live demo or screenshots.
