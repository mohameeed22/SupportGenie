"""
dashboard.py — Streamlit live analytics dashboard for SupportGenie.

Usage:
    streamlit run dashboard.py
"""

from __future__ import annotations

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="SupportGenie Dashboard", layout="wide")
st.title("📊 SupportGenie Live Dashboard")

try:
    from db import session_store

    session_store.initialize()
except Exception as exc:
    st.error(f"Could not connect to database: {exc}")
    st.stop()


@st.cache_data(ttl=30)
def load_stats():
    return {
        "users": session_store.count_users(),
        "questions": session_store.count_events("question"),
        "escalations": session_store.count_events("escalation"),
        "open_tickets": session_store.count_support_tickets(status="open"),
        "resolved_tickets": session_store.count_support_tickets(status="resolved"),
        "image_queries": session_store.count_events("image_query"),
        "voice_queries": session_store.count_events("voice_queries"),
        "csat": session_store.get_csat_stats(),
        "top_questions": session_store.top_questions(10),
    }


@st.cache_data(ttl=30)
def load_recent_tickets():
    return session_store.list_support_tickets(limit=20)


stats = load_stats()
tickets = load_recent_tickets()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("👥 Users", stats["users"])
col2.metric("💬 Questions", stats["questions"])
col3.metric("🚨 Escalations", stats["escalations"])
col4.metric("🎫 Open Tickets", stats["open_tickets"])
col5.metric("✅ Resolved", stats["resolved_tickets"])

st.divider()

csat = stats["csat"]
if csat["count"] > 0:
    col_a, col_b = st.columns(2)
    col_a.metric("⭐ CSAT Average", f'{csat["average"]:.2f} / 5', delta=f"{csat['count']} ratings")
    with col_b:
        dist = csat.get("distribution", {})
        st.write("**Rating Distribution**")
        for rating in ["1", "2", "3", "4", "5"]:
            count = dist.get(rating, 0)
            if count > 0:
                st.write(f"{'⭐' * int(rating)}: {count}")
else:
    st.info("No CSAT ratings yet.")

st.divider()

st.subheader("🔝 Top Questions")
top_q = stats["top_questions"]
if top_q:
    for q in top_q:
        st.write(f"- **{q['question']}** ({q['total']}×)")
else:
    st.write("No questions logged yet.")

st.subheader("📋 Recent Tickets")
if tickets:
    for t in tickets:
        status_emoji = "🟢" if t["status"] == "open" else "🔴" if t["status"] == "resolved" else "🟡"
        st.write(f"{status_emoji} **#{t['ticket_id']}** — {t.get('subject', 'N/A')} — `{t['user_id']}` — {t.get('updated_at', '')[:16]}")
else:
    st.write("No tickets yet.")

st.caption("Auto-refreshes every 30 seconds. Data from SQLite database.")
