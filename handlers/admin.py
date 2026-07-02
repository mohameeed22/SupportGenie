"""Admin-only commands for stats and broadcast."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

import config
from analytics import dashboard_summary
from db import session_store


def _is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_USER_IDS


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text("This command is restricted to admins.")
        return

    stats = dashboard_summary()
    top_questions = stats["top_questions"]
    top_block = (
        "\n".join(f"• {row['question']} ({row['total']})" for row in top_questions)
        or "• No questions logged yet"
    )

    await update.message.reply_text(
        "📊 *SupportGenie Stats*\n\n"
        f"Users: *{stats['users']}*\n"
        f"Questions: *{stats['questions']}*\n"
        f"Escalations: *{stats['escalations']}*\n"
        f"Escalation rate: *{stats['escalation_rate']}%*\n\n"
        f"*Top questions*\n{top_block}",
        parse_mode="Markdown",
    )


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text("This command is restricted to admins.")
        return

    message_text = ""
    if update.message.reply_to_message and update.message.reply_to_message.text:
        message_text = update.message.reply_to_message.text
    elif context.args:
        message_text = " ".join(context.args).strip()

    if not message_text:
        await update.message.reply_text(
            "Usage: /broadcast <message> or reply to a message with /broadcast"
        )
        return

    user_ids = session_store.get_all_user_ids()
    sent = 0
    for user_id in user_ids:
        try:
            await context.bot.send_message(chat_id=user_id, text=message_text)
            sent += 1
        except Exception:
            continue

    await update.message.reply_text(f"Broadcast sent to {sent} users.")
