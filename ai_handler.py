"""
ai_handler.py — Groq AI integration for NovaBuy support bot.

Manages per-user conversation history (last 10 exchanges) and sends
messages to Groq's Llama model with the NovaBuy system prompt injected.
"""

import logging
from collections import defaultdict
from groq import AsyncGroq

import config
from store_context import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# ── Groq client ───────────────────────────────────────────────────────────────
_client = AsyncGroq(api_key=config.GROQ_API_KEY)

# ── Per-user conversation history: {user_id: [{"role": ..., "content": ...}]}
_histories: dict[int, list[dict]] = defaultdict(list)

MAX_HISTORY = 10  # number of message pairs to remember


def clear_history(user_id: int) -> None:
    """Reset conversation history for a user (e.g., on /start)."""
    _histories[user_id] = []


async def get_ai_response(user_id: int, user_message: str) -> str:
    """
    Send a user message to Groq and return the assistant's reply.
    Maintains a rolling conversation history per user.
    """
    history = _histories[user_id]

    # Append the new user message
    history.append({"role": "user", "content": user_message})

    # Build the full message list: system prompt + history
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    try:
        response = await _client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            temperature=0.5,
            max_tokens=512,
        )
        reply = response.choices[0].message.content.strip()

    except Exception as e:
        logger.error("Groq API error: %s", e)
        reply = (
            "Sorry, I'm having trouble connecting right now. "
            "Please try again in a moment, or tap *Talk to a Human* for immediate help."
        )

    # Append assistant reply to history
    history.append({"role": "assistant", "content": reply})

    # Trim history to last MAX_HISTORY pairs
    if len(history) > MAX_HISTORY * 2:
        _histories[user_id] = history[-(MAX_HISTORY * 2):]

    return reply
