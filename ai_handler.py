from __future__ import annotations

import json
import logging
import time
from typing import Any

from groq import AsyncGroq

import config
from db import session_store
from store_context import build_system_prompt, detect_language
from tools import execute_tool, get_tool_definitions

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

    rag_context = ""
    if config.RAG_ENABLED:
        try:
            from rag import relevance_search

            rag_context = relevance_search(user_message)
        except Exception as exc:
            logger.warning("RAG retrieval failed: %s", exc)

    extra = extra_context or ""
    if rag_context:
        extra = f"{extra_context}\n\nRelevant product/policy info:\n{rag_context}" if extra_context else f"Relevant product/policy info:\n{rag_context}"

    system_prompt = build_system_prompt(
        preferred_language=language,
        user_name=profile.get("full_name"),
        extra_context=extra or None,
    )

    return (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": user_message}]
    )


async def _call_with_tools(
    messages: list[dict[str, str]],
    user_id: int,
    max_tool_rounds: int = 5,
) -> str:
    tools = get_tool_definitions()
    for _round in range(max_tool_rounds):
        response = await _client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.3,
            max_tokens=1024,
        )

        choice = response.choices[0]
        msg = choice.message

        if not msg.tool_calls:
            content = msg.content or ""
            messages.append({"role": "assistant", "content": content})
            return content.strip()

        messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": [{"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in msg.tool_calls]})

        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            result = await execute_tool(name, args, user_id=user_id)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    final = await _client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=512,
    )
    return (final.choices[0].message.content or "").strip()


async def _call_without_tools(messages: list[dict[str, str]]) -> str:
    response = await _client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=messages,
        temperature=0.4,
        max_tokens=512,
    )
    return (response.choices[0].message.content or "").strip()


async def _stream_with_tools(
    messages: list[dict[str, str]],
    user_id: int,
    stream_message: Any,
    max_tool_rounds: int = 5,
) -> str:
    tools = get_tool_definitions()
    for _round in range(max_tool_rounds):
        response = await _client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.3,
            max_tokens=1024,
        )

        choice = response.choices[0]
        msg = choice.message

        if not msg.tool_calls:
            content = msg.content or ""
            messages.append({"role": "assistant", "content": content})

            await stream_message.edit_text(content or "...")
            return content.strip()

        messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": [{"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in msg.tool_calls]})

        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            result = await execute_tool(name, args, user_id=user_id)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    final = await _client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=512,
    )
    return (final.choices[0].message.content or "").strip()


async def _stream_completion(messages: list[dict[str, str]], stream_message: Any) -> str:
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
        now = time.monotonic()
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
            reply = await _stream_with_tools(messages, user_id, stream_message)
        else:
            reply = await _call_with_tools(messages, user_id)
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
