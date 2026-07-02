"""Analytics helpers for SupportGenie."""

from __future__ import annotations

from db import session_store


def dashboard_summary() -> dict[str, object]:
    return {
        "users": session_store.count_users(),
        "questions": session_store.count_events("question"),
        "escalations": session_store.count_events("escalation"),
        "escalation_rate": session_store.escalation_rate(),
        "top_questions": session_store.top_questions(),
    }
