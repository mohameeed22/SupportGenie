"""Groq AI integration for SupportGenie."""

from __future__ import annotations

import logging
from typing import Any

from groq import AsyncGroq

import config
from db import session_store
from store_context import build_system_prompt, detect_language

logger = logging.getLogger(__name__)

_client = AsyncGroq(api_key=config.GROQ_API_KEY)
MAX_HISTORY_MESSAGES = 20


def clear_history(user_id: int) -> None:
    session_store.clear_conversation(user_id)


def _build_messages(
    user_id: int,
    user_message: str,
    *,
    extra_context: str | None = None,
    preferred_language: str | None = None,
) -> list[dict[str, str]]:
    profile = session_store.get_user_profile(user_id) or {}
    language = preferred_language or detect_language(user_message)
    history = session_store.get_recent_messages(user_id, limit=MAX_HISTORY_MESSAGES)
    system_prompt = build_system_prompt(
        preferred_language=language,
        user_name=profile.get("full_name"),
        extra_context=extra_context,
    )
    return [{"role": "system", "content": system_prompt}] + history + [
        {"role": "user", "content": user_message}
    ]


async def _create_completion(messages: list[dict[str, str]]) -> str:
    response = await _client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=messages,
        temperature=0.4,
        max_tokens=512,
    )
    content = response.choices[0].message.content or ""
    return content.strip()


async def _stream_completion(
    messages: list[dict[str, str]],
    *,
    stream_message: Any,
) -> str:
    stream = await _client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=messages,
        temperature=0.4,
        max_tokens=512,
        stream=True,
    )

    buffer = []
    last_edit = 0.0
    async for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if not delta:
            continue
        buffer.append(delta)
        now = __import__("time").monotonic()
        if now - last_edit >= 0.6:
            await stream_message.edit_text("".join(buffer))
            last_edit = now

    reply = "".join(buffer).strip()
    await stream_message.edit_text(reply or "...")
    return reply


async def get_ai_response(
    user_id: int,
    user_message: str,
    *,
    extra_context: str | None = None,
    stream_message: Any | None = None,
    preferred_language: str | None = None,
) -> str:
    language = preferred_language or detect_language(user_message)
    session_store.record_user_message(
        user_id,
        user_message,
        preferred_language=language,
    )

    messages = _build_messages(
        user_id,
        user_message,
        extra_context=extra_context,
        preferred_language=language,
    )

    try:
        if stream_message is not None:
            reply = await _stream_completion(messages, stream_message=stream_message)
        else:
            reply = await _create_completion(messages)
    except Exception as exc:
        logger.exception("Groq API error")
        reply = (
            "Sorry, I'm having trouble connecting right now. "
            "Please try again in a moment, or tap *Talk to a Human* for immediate help."
        )
        session_store.record_event(
            user_id,
            "ai_error",
            question=user_message,
            details={"error": str(exc)},
        )

    session_store.record_assistant_message(user_id, reply)
    session_store.record_event(
        user_id,
        "question",
        question=user_message,
        answer=reply,
        details={"language": language, "context": extra_context or ""},
    )
    return reply
