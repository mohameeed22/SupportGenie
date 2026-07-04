from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import config

logger = logging.getLogger(__name__)

_LOCK = threading.RLock()
_CONNECTION: sqlite3.Connection | None = None


def _resolve_db_path() -> Path:
    raw = os.getenv("SUPPORTGENIE_DB_PATH") or config.DB_PATH or "supportgenie.db"
    path = Path(raw)
    if raw == ":memory:":
        return Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent.parent / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


DB_PATH = None


def _connect() -> sqlite3.Connection:
    path = _resolve_db_path()
    conn = sqlite3.connect(path.as_posix(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _ensure_connection() -> sqlite3.Connection:
    global _CONNECTION
    if _CONNECTION is None:
        with _LOCK:
            if _CONNECTION is None:
                _CONNECTION = _connect()
                _initialize_schema(_CONNECTION)
    return _CONNECTION


def _initialize_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            preferred_language TEXT,
            is_admin INTEGER NOT NULL DEFAULT 0,
            message_count INTEGER NOT NULL DEFAULT 0,
            escalation_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            event_type TEXT NOT NULL,
            question TEXT,
            answer TEXT,
            details TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS support_tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            source TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            reason TEXT,
            order_id TEXT,
            transcript TEXT,
            metadata TEXT,
            assigned_to TEXT,
            resolution_note TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            resolved_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS csat_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ticket_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
            created_at TEXT NOT NULL
        );
        """
    )
    conn.commit()


def initialize() -> None:
    _ensure_connection()


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def get_user_profile(user_id: int) -> dict[str, Any] | None:
    row = (
        _ensure_connection()
        .execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,),
        )
        .fetchone()
    )
    return dict(row) if row else None


def upsert_user(
    user_id: int,
    *,
    username: str | None = None,
    full_name: str | None = None,
    preferred_language: str | None = None,
    is_admin: bool | None = None,
    bump_messages: bool = False,
) -> None:
    conn = _ensure_connection()
    existing = get_user_profile(user_id)
    now = _now()

    if existing is None:
        conn.execute(
            """
            INSERT INTO users (
                user_id, username, full_name, preferred_language, is_admin,
                message_count, escalation_count, created_at, last_seen_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                username,
                full_name,
                preferred_language,
                1 if is_admin else 0,
                1 if bump_messages else 0,
                0,
                now,
                now,
                now,
            ),
        )
    else:
        conn.execute(
            """
            UPDATE users
            SET
                username = COALESCE(?, username),
                full_name = COALESCE(?, full_name),
                preferred_language = COALESCE(?, preferred_language),
                is_admin = COALESCE(?, is_admin),
                message_count = message_count + ?,
                last_seen_at = ?,
                updated_at = ?
            WHERE user_id = ?
            """,
            (
                username,
                full_name,
                preferred_language,
                None if is_admin is None else (1 if is_admin else 0),
                1 if bump_messages else 0,
                now,
                now,
                user_id,
            ),
        )
    conn.commit()


def record_user_message(
    user_id: int,
    content: str,
    *,
    username: str | None = None,
    full_name: str | None = None,
    preferred_language: str | None = None,
) -> None:
    upsert_user(
        user_id,
        username=username,
        full_name=full_name,
        preferred_language=preferred_language,
        bump_messages=True,
    )
    conn = _ensure_connection()
    conn.execute(
        "INSERT INTO messages (user_id, role, content, created_at) VALUES (?, 'user', ?, ?)",
        (user_id, content, _now()),
    )
    conn.commit()


def record_assistant_message(user_id: int, content: str) -> None:
    upsert_user(user_id)
    conn = _ensure_connection()
    conn.execute(
        "INSERT INTO messages (user_id, role, content, created_at) VALUES (?, 'assistant', ?, ?)",
        (user_id, content, _now()),
    )
    conn.commit()


def clear_conversation(user_id: int) -> None:
    conn = _ensure_connection()
    conn.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
    conn.commit()


def get_recent_messages(user_id: int, limit: int = 20) -> list[dict[str, str]]:
    rows = (
        _ensure_connection()
        .execute(
            """
        SELECT role, content
        FROM messages
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
            (user_id, limit),
        )
        .fetchall()
    )
    return [dict(row) for row in reversed(rows)]


def record_event(
    user_id: int | None,
    event_type: str,
    *,
    question: str | None = None,
    answer: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    conn = _ensure_connection()
    conn.execute(
        """
        INSERT INTO analytics (user_id, event_type, question, answer, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            event_type,
            question,
            answer,
            json.dumps(details) if details else None,
            _now(),
        ),
    )
    if event_type == "escalation" and user_id is not None:
        conn.execute(
            "UPDATE users SET escalation_count = escalation_count + 1, updated_at = ? WHERE user_id = ?",
            (_now(), user_id),
        )
    conn.commit()


def record_feedback(user_id: int, helpful: bool, *, source: str = "general") -> None:
    record_event(
        user_id,
        "feedback",
        details={"helpful": helpful, "source": source},
    )


def record_escalation(user_id: int, *, reason: str, source: str = "general") -> None:
    record_event(
        user_id,
        "escalation",
        details={"reason": reason, "source": source},
    )


def record_csat(user_id: int, ticket_id: int, rating: int) -> None:
    conn = _ensure_connection()
    conn.execute(
        "INSERT INTO csat_ratings (user_id, ticket_id, rating, created_at) VALUES (?, ?, ?, ?)",
        (user_id, ticket_id, rating, _now()),
    )
    conn.commit()


def _get_user_tier(user_id: int) -> str:
    profile = get_user_profile(user_id)
    if not profile:
        return "anonymous"
    if profile.get("message_count", 0) >= 5:
        return "known"
    return "anonymous"


def _get_known_users() -> set[int]:
    rows = (
        _ensure_connection()
        .execute("SELECT user_id FROM users WHERE message_count >= 5")
        .fetchall()
    )
    return {int(row["user_id"]) for row in rows}


def user_message_rate_limited(
    user_id: int,
    max_messages: int | None = None,
    window_seconds: int | None = None,
) -> bool:
    tier = _get_user_tier(user_id)
    tier_config = config.RATE_LIMIT_TIERS.get(tier, {})

    if max_messages is None:
        max_messages = tier_config.get("max", config.RATE_LIMIT_MAX_MESSAGES)
    if window_seconds is None:
        window_seconds = tier_config.get("window", config.RATE_LIMIT_WINDOW_SECONDS)

    since = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
    row = (
        _ensure_connection()
        .execute(
            """
        SELECT COUNT(*) AS total
        FROM messages
        WHERE user_id = ? AND role = 'user' AND created_at >= ?
        """,
            (user_id, since.strftime("%Y-%m-%d %H:%M:%S")),
        )
        .fetchone()
    )
    return bool(row and row["total"] >= max_messages)


def count_users() -> int:
    row = _ensure_connection().execute("SELECT COUNT(*) AS total FROM users").fetchone()
    return int(row["total"]) if row else 0


def count_events(event_type: str) -> int:
    row = (
        _ensure_connection()
        .execute(
            "SELECT COUNT(*) AS total FROM analytics WHERE event_type = ?",
            (event_type,),
        )
        .fetchone()
    )
    return int(row["total"]) if row else 0


def top_questions(limit: int = 5) -> list[dict[str, Any]]:
    rows = (
        _ensure_connection()
        .execute(
            """
        SELECT COALESCE(question, '') AS question, COUNT(*) AS total
        FROM analytics
        WHERE event_type = 'question' AND question IS NOT NULL AND question != ''
        GROUP BY question
        ORDER BY total DESC, question ASC
        LIMIT ?
        """,
            (limit,),
        )
        .fetchall()
    )
    return [dict(row) for row in rows]


def get_all_user_ids() -> list[int]:
    rows = (
        _ensure_connection()
        .execute("SELECT user_id FROM users ORDER BY last_seen_at DESC")
        .fetchall()
    )
    return [int(row["user_id"]) for row in rows]


def escalation_rate() -> float:
    users = count_users()
    if users == 0:
        return 0.0
    return round(count_events("escalation") / users * 100, 2)


def create_support_ticket(
    user_id: int,
    subject: str,
    *,
    source: str = "general",
    reason: str | None = None,
    order_id: str | None = None,
    transcript: list[dict[str, str]] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    conn = _ensure_connection()
    now = _now()
    cursor = conn.execute(
        """
        INSERT INTO support_tickets (
            user_id, subject, source, status, reason, order_id, transcript,
            metadata, created_at, updated_at
        ) VALUES (?, ?, ?, 'open', ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            subject,
            source,
            reason,
            order_id,
            json.dumps(transcript or []),
            json.dumps(metadata or {}),
            now,
            now,
        ),
    )
    conn.commit()
    ticket_id = int(cursor.lastrowid)
    record_event(
        user_id,
        "support_ticket_created",
        question=subject,
        details={
            "ticket_id": ticket_id,
            "source": source,
            "reason": reason or "",
            "order_id": order_id or "",
        },
    )
    return get_support_ticket(ticket_id) or {}


def _support_ticket_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    for key in ("transcript", "metadata"):
        raw = data.get(key)
        if raw:
            try:
                data[key] = json.loads(raw)
            except json.JSONDecodeError:
                pass
    return data


def get_support_ticket(ticket_id: int) -> dict[str, Any] | None:
    row = (
        _ensure_connection()
        .execute(
            "SELECT * FROM support_tickets WHERE ticket_id = ?",
            (ticket_id,),
        )
        .fetchone()
    )
    return _support_ticket_row_to_dict(row) if row else None


def list_support_tickets(
    *, status: str | None = None, limit: int = 10
) -> list[dict[str, Any]]:
    query = "SELECT * FROM support_tickets"
    params: list[Any] = []
    if status:
        query += " WHERE status = ?"
        params.append(status)
    query += " ORDER BY updated_at DESC, ticket_id DESC LIMIT ?"
    params.append(limit)
    rows = _ensure_connection().execute(query, params).fetchall()
    return [_support_ticket_row_to_dict(row) for row in rows]


def update_support_ticket(
    ticket_id: int,
    *,
    status: str | None = None,
    assigned_to: str | None = None,
    resolution_note: str | None = None,
) -> dict[str, Any] | None:
    ticket = get_support_ticket(ticket_id)
    if not ticket:
        return None

    updates: list[str] = []
    values: list[Any] = []
    if status is not None:
        updates.append("status = ?")
        values.append(status)
        if status.lower() == "resolved":
            updates.append("resolved_at = ?")
            values.append(_now())
    if assigned_to is not None:
        updates.append("assigned_to = ?")
        values.append(assigned_to)
    if resolution_note is not None:
        updates.append("resolution_note = ?")
        values.append(resolution_note)

    if not updates:
        return ticket

    updates.append("updated_at = ?")
    values.append(_now())
    values.append(ticket_id)

    _ensure_connection().execute(
        f"UPDATE support_tickets SET {', '.join(updates)} WHERE ticket_id = ?",
        values,
    )
    _ensure_connection().commit()
    return get_support_ticket(ticket_id)


def count_support_tickets(*, status: str | None = None) -> int:
    query = "SELECT COUNT(*) AS total FROM support_tickets"
    params: list[Any] = []
    if status:
        query += " WHERE status = ?"
        params.append(status)
    row = _ensure_connection().execute(query, params).fetchone()
    return int(row["total"]) if row else 0


def get_csat_stats() -> dict[str, float]:
    rows = (
        _ensure_connection()
        .execute("SELECT rating FROM csat_ratings")
        .fetchall()
    )
    if not rows:
        return {"count": 0, "average": 0.0, "distribution": {}}
    ratings = [r["rating"] for r in rows]
    dist = {}
    for r in ratings:
        dist[str(r)] = dist.get(str(r), 0) + 1
    return {
        "count": len(ratings),
        "average": round(sum(ratings) / len(ratings), 2),
        "distribution": dist,
    }
