from __future__ import annotations

import logging
from typing import Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import config
from db import session_store

logger = logging.getLogger(__name__)

_USER_SESSIONS: dict[int, dict[str, Any]] = {}


def _make_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🏠 Back to Menu", callback_data="menu:main")]]
    )


async def human_escalation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    transcript = session_store.get_recent_messages(user.id, limit=12)
    ticket = session_store.create_support_ticket(
        user.id,
        subject="Human support request",
        source="telegram-escalation",
        reason="user-request" if update.callback_query else "ai-escalation",
        transcript=transcript,
        metadata={"username": user.username, "full_name": user.full_name},
    )

    ticket_id = ticket.get("ticket_id", "pending")

    text = (
        "🧑‍💼 *Connecting you with our support team*\n\n"
        f"📧 Email: *{config.SUPPORT_EMAIL}*\n"
        f"🕐 Hours: {config.SUPPORT_HOURS}\n"
        f"⚡ Response time: Within 4 hours\n\n"
        f"🎫 Ticket ID: *#{ticket_id}*\n\n"
        "Please include your *Order ID* and a description of your issue for faster service."
    )

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.chat.send_action("typing")
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=_make_back_keyboard())
    else:
        await update.message.chat.send_action("typing")
        await update.message.reply_text(text, parse_mode="Markdown")

    logger.info(
        "ESCALATION — User %s (@%s, ID: %s) requested human support. Ticket #%s",
        user.full_name, user.username, user.id, ticket_id,
    )

    if config.SUPPORT_GROUP_CHAT_ID:
        _USER_SESSIONS[user.id] = {"ticket_id": ticket_id, "active": True}
        try:
            await context.bot.send_message(
                chat_id=config.SUPPORT_GROUP_CHAT_ID,
                text=(
                    f"🎫 *New Support Ticket #{ticket_id}*\n\n"
                    f"👤 User: {user.full_name} (@{user.username})\n"
                    f"🆔 ID: `{user.id}`\n\n"
                    f"Reply to this message to respond to the user directly.\n"
                    f"Use `/close_{ticket_id}` to resolve the ticket."
                ),
                parse_mode="Markdown",
            )
        except Exception as exc:
            logger.warning("Failed to forward to support group: %s", exc)


async def forward_from_support_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not config.SUPPORT_GROUP_CHAT_ID:
        return
    if not update.message or not update.message.text:
        return
    if update.effective_chat.id != config.SUPPORT_GROUP_CHAT_ID:
        return

    text = update.message.text.strip()

    if text.startswith("/close_"):
        try:
            ticket_id = int(text.replace("/close_", "").strip())
            ticket = session_store.get_support_ticket(ticket_id)
            if ticket:
                session_store.update_support_ticket(ticket_id, status="resolved", resolution_note="Closed via support group")
                await update.message.reply_text(f"Ticket #{ticket_id} resolved.")
                user_id = ticket.get("user_id")
                if user_id:
                    try:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=f"✅ Your support ticket *#{ticket_id}* has been resolved. Thanks for your patience!",
                            parse_mode="Markdown",
                        )
                    except Exception:
                        pass
                _USER_SESSIONS.pop(user_id, None)
            else:
                await update.message.reply_text(f"Ticket #{ticket_id} not found.")
        except ValueError:
            await update.message.reply_text("Usage: /close_<ticket_id>")
        return

    reply = update.message.reply_to_message
    if not reply:
        return

    for uid, session in list(_USER_SESSIONS.items()):
        if not session.get("active"):
            continue
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=f"🧑‍💼 *Support Agent:*\n{text}",
                parse_mode="Markdown",
            )
            session_store.record_assistant_message(uid, f"[Support Agent]: {text}")
            await update.message.reply_text(f"✅ Message forwarded to user {uid}.")
            return
        except Exception as exc:
            logger.warning("Failed to forward to user %s: %s", uid, exc)
            _USER_SESSIONS[uid]["active"] = False

    await update.message.reply_text("Could not find an active session for the replied message.")
