---
name: Hackathon Task Template
about: Template for hackathon tasks with scope, in-scope/out-of-scope, success criteria,
  and deadline.
title: "[TASK] "
labels: ''
assignees: ''

---

## Task Title
(Short, clear description of the task)

## Objective
Answer HR resource queries via RAG.

## In-Scope
- Synthetic dataset (15–25 employees)
- Retrieval (keyword + semantic)
- FastAPI backend
- Simple UI (Streamlit or minimal web)
- Documentation + demo

## Out-of-Scope
- Real PII data
- Authentication or HRIS integrations
- Complex analytics/dashboard

## Success Criteria
- Retrieval hit@k > 80%
- Latency: Local ≤ 3s, Deployed ≤ 5s
- Response is relevant, explains match reason

## Deadline
- Day 1: MVP
- Day 2: Polish + Deploy

## Checklist
- [ ] Code implemented
- [ ] Tested with sample queries
- [ ] Documentation updated
