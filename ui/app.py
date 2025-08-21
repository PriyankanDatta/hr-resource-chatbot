# ui/app.py
import os
import json
import requests
import streamlit as st

API_BASE = os.environ.get("API_BASE", "http://127.0.0.1:8000")

st.set_page_config(page_title="HR Resource Chatbot", layout="centered")
st.title("HR Resource Chatbot")

with st.sidebar:
    st.subheader("Filters (optional)")
    skill = st.text_input("Skill")
    min_exp = st.number_input("Min years", min_value=0, step=1)
    domain = st.text_input("Domain")
    availability = st.selectbox("Availability", ["", "available", "soon", "unavailable"])
    top_k = st.slider("Candidates (k)", 1, 10, 3)

st.markdown("Type a requirement, e.g. **python aws 3+ years ecommerce available**")

query = st.text_input("Your request", key="query", placeholder="e.g., backend docker postgres 3+ years available")
go = st.button("Send")

def build_query_with_filters(q: str) -> str:
    parts = [q.strip()]
    if skill: parts.append(skill)
    if min_exp: parts.append(f"{int(min_exp)}+ years")
    if domain: parts.append(domain)
    if availability: parts.append(availability)
    return " ".join([p for p in parts if p])

def call_chat(q: str, k: int):
    url = f"{API_BASE}/chat"
    payload = {"query": q, "top_k": k}
    r = requests.post(url, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()

def call_keyword_list():
    # Optional list view from filters only
    params = {}
    if skill: params["skill"] = skill
    if min_exp: params["min_experience"] = int(min_exp)
    if domain: params["domain"] = domain
    if availability: params["availability"] = availability
    params["top_k"] = top_k
    url = f"{API_BASE}/employees/search"
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    return r.json()

if go:
    try:
        q = build_query_with_filters(query)
        with st.spinner("Thinking..."):
            data = call_chat(q, top_k)
        st.success("Response")
        st.write(data.get("response_text", ""))

        used_ids = set(data.get("used_candidate_ids", []))
        if used_ids:
            st.subheader("Candidates")
            # Lightweight fetch of details: reuse /employees/search to get “why” if filters present
            # Fallback: show IDs if we don’t fetch details.
            try:
                list_data = call_keyword_list()
                pool = {c["id"]: c for c in list_data.get("results", [])}
            except Exception:
                pool = {}

            for cid in used_ids:
                c = pool.get(cid)
                with st.container(border=True):
                    st.markdown(f"**ID {cid}**")
                    if c:
                        st.markdown(f"**Name:** {c['name']}")
                        if c.get("why"):
                            st.markdown(f"**Why matched:** {c['why']}")
                    else:
                        st.caption("Details not fetched; refine filters to see ‘why matched’.")
    except requests.HTTPError as e:
        st.error(f"API error: {e.response.status_code} — {e.response.text}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")
