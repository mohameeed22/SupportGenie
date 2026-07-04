from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from db import session_store

logger = logging.getLogger(__name__)


async def handle_csat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    if len(parts) != 3 or parts[0] != "csat":
        return

    try:
        ticket_id = int(parts[1])
        rating = int(parts[2])
    except (ValueError, IndexError):
        return

    session_store.record_event(
        update.effective_user.id,
        "csat_rating",
        details={"ticket_id": ticket_id, "rating": rating},
    )

    messages = {
        1: "We're sorry to hear that. Your feedback will help us improve.",
        2: "Thanks for your honesty. We'll work on getting better.",
        3: "Thanks for your feedback! We're always improving.",
        4: "Glad to hear it! We appreciate your support.",
        5: "Amazing! 😊 Thanks for the perfect rating!",
    }

    text = messages.get(rating, "Thanks for your feedback!")
    await query.edit_message_text(f"{text}\n\n*Ticket #{ticket_id}* — Rating: {rating}/5", parse_mode="Markdown")
