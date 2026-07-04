from __future__ import annotations

from db import session_store


def dashboard_summary() -> dict:
    return {
        "users": session_store.count_users(),
        "questions": session_store.count_events("question"),
        "escalations": session_store.count_events("escalation"),
        "escalation_rate": session_store.escalation_rate(),
        "top_questions": session_store.top_questions(),
        "csat": session_store.get_csat_stats(),
        "open_tickets": session_store.count_support_tickets(status="open"),
        "image_queries": session_store.count_events("image_query"),
        "voice_queries": session_store.count_events("voice_query"),
    }
