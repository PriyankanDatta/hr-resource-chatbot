# ui/app.py
import os
import requests
import streamlit as st

API_BASE = os.environ.get("API_BASE", "http://127.0.0.1:8000")

st.set_page_config(page_title="HR Resource Chatbot", layout="centered")
st.title("HR Resource Chatbot")

# ---------- Sidebar Filters ----------
with st.sidebar:
    st.subheader("Filters (optional)")
    skill = st.text_input("Skill")
    min_exp = st.number_input("Min years", min_value=0, step=1)
    domain = st.text_input("Domain")
    availability = st.selectbox("Availability", ["", "available", "soon", "unavailable"])
    top_k = st.slider("Candidates (k)", 1, 10, 3)

st.markdown("Type a requirement, e.g. **python aws 3+ years ecommerce available**")

query = st.text_input(
    "Your request",
    key="query",
    placeholder="e.g., backend docker postgres 3+ years available"
)
go = st.button("Send")

# ---------- Helpers ----------
def build_query_with_filters(q: str) -> str:
    parts = [q.strip()]
    if skill:
        parts.append(skill)
    if min_exp:
        parts.append(f"{int(min_exp)}+ years")
    if domain:
        parts.append(domain)
    if availability:
        parts.append(availability)
    return " ".join([p for p in parts if p])

def call_chat(q: str, k: int):
    url = f"{API_BASE}/chat"
    payload = {"query": q, "top_k": k}
    r = requests.post(url, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()

def call_hybrid(q: str, k: int):
    url = f"{API_BASE}/search/hybrid"
    params = {"q": q, "top_k": k}
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    return r.json()

def call_keyword_list():
    params = {}
    if skill:
        params["skill"] = skill
    if min_exp:
        params["min_experience"] = int(min_exp)
    if domain:
        params["domain"] = domain
    if availability:
        params["availability"] = availability
    params["top_k"] = top_k
    url = f"{API_BASE}/employees/search"
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    return r.json()

def render_candidate_card(c: dict):
    st.markdown("----")
    title = f"{c.get('name', 'Unknown')} (ID {c.get('id','?')})"
    st.subheader(title)

    meta = c.get("meta") or {}
    skills = meta.get("skills", [])
    years = meta.get("experience_years", None)
    projects = meta.get("projects", [])
    avail = meta.get("availability", None)

    why = c.get("why") or c.get("reason_kw") or c.get("reason_sem")

    if skills:
        st.write(f"**Skills:** {', '.join(skills[:5])}")
    if years is not None:
        st.write(f"**Experience:** {years} years")
    if projects:
        st.write(f"**Projects:** {', '.join(projects[:2])}")
    if avail:
        st.write(f"**Availability:** {avail}")

    if why:
        st.info(f"Why matched: {why}")

# ---------- Empty state (before first Send) ----------
if not go and not query.strip():
    st.info(
        "Try a request like:\n"
        "- python aws 3+ years ecommerce available\n"
        "- react native mobile app 4+ years\n"
        "- available healthcare nlp\n"
        "- backend docker postgres\n"
    )

# ---------- Main Action ----------
if go:
    try:
        q = build_query_with_filters(query)
        with st.spinner("Thinking..."):
            chat_out = call_chat(q, top_k)

        # Response block
        resp_text = chat_out.get("response_text", "").strip()
        if resp_text:
            st.success("Response")
            st.write(resp_text)
        else:
            st.warning("No response text returned.")
            if st.button("Retry"):
                st.rerun()

        # Candidate cards
        used_ids = list(dict.fromkeys(chat_out.get("used_candidate_ids", [])))  # preserve order
        if used_ids:
            st.subheader("Candidates")

            # Try hybrid to get rich metadata for the SAME query
            hybrid_pool = {}
            try:
                hyb = call_hybrid(q, max(top_k, 10))
                for r in hyb.get("results", []):
                    hybrid_pool[r["id"]] = r
            except Exception:
                hybrid_pool = {}

            # Try baseline wrapper to get 'why' if filters were set
            baseline_pool = {}
            try:
                lst = call_keyword_list()
                baseline_pool = {c["id"]: c for c in lst.get("results", [])}
            except Exception:
                baseline_pool = {}

            for cid in used_ids:
                merged = {"id": cid}
                if cid in hybrid_pool:
                    merged.update(hybrid_pool[cid])
                if cid in baseline_pool:
                    merged.setdefault("name", baseline_pool[cid].get("name"))
                    merged.setdefault("why", baseline_pool[cid].get("why"))
                with st.container(border=True):
                    render_candidate_card(merged)
        else:
            # No matches state
            st.warning(
                "No candidates matched strongly. Try one of:\n"
                "- Lower min years (e.g., 5+ → 3+)\n"
                "- Remove availability filter or choose 'soon'\n"
                "- Add a domain (e.g., ecommerce, healthcare)"
            )
            if st.button("Retry"):
                st.rerun()

    except requests.HTTPError as e:
        st.error(f"API error: {e.response.status_code} — {e.response.text}")
        if st.button("Retry"):
            st.rerun()
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        if st.button("Retry"):
            st.rerun()
