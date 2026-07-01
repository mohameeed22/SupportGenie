"""Feedback keyboard and handler."""

from __future__ import annotations

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import config
from db import session_store

logger = logging.getLogger(__name__)


def feedback_keyboard(*, source: str = "general") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("👍 Yes", callback_data=f"feedback:yes:{source}"),
                InlineKeyboardButton("👎 No", callback_data=f"feedback:no:{source}"),
            ]
        ]
    )


async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    helpful = parts[1] == "yes"
    source = parts[2] if len(parts) > 2 else "general"

    session_store.record_feedback(update.effective_user.id, helpful, source=source)

    if helpful:
        await query.edit_message_reply_markup(reply_markup=None)
        return

    await query.message.reply_text(
        "🧑‍💼 *Connecting you with our support team*\n\n"
        f"📧 Email: *{config.SUPPORT_EMAIL}*\n"
        f"🕐 Hours: {config.SUPPORT_HOURS}\n"
        "Please include your Order ID if you have one.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🧑‍💼 Talk to a Human", callback_data="menu:human")]]
        ),
    )

