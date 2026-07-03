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


def _format_ticket(ticket: dict) -> str:
    transcript_size = len(ticket.get("transcript") or [])
    return (
        f"🎫 *Ticket #{ticket['ticket_id']}*\n"
        f"Status: *{ticket['status']}*\n"
        f"User: `{ticket['user_id']}`\n"
        f"Source: {ticket.get('source', 'unknown')}\n"
        f"Subject: {ticket.get('subject', 'N/A')}\n"
        f"Order: {ticket.get('order_id') or 'N/A'}\n"
        f"Transcript messages: {transcript_size}\n"
        f"Updated: {ticket.get('updated_at', 'N/A')}"
    )


async def inbox_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text("This command is restricted to admins.")
        return

    tickets = session_store.list_support_tickets(status="open", limit=10)
    if not tickets:
        await update.message.reply_text("No open support tickets.")
        return

    lines = ["📥 *Open Support Inbox*", ""]
    for ticket in tickets:
        lines.append(
            f"• #{ticket['ticket_id']} {ticket.get('subject', 'Support request')} — user {ticket['user_id']}"
        )
        lines.append(f"  {ticket.get('source', 'unknown')} · {ticket.get('updated_at', 'N/A')}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def ticket_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text("This command is restricted to admins.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /ticket <ticket_id>")
        return

    try:
        ticket_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Ticket ID must be a number.")
        return

    ticket = session_store.get_support_ticket(ticket_id)
    if not ticket:
        await update.message.reply_text(f"Ticket #{ticket_id} not found.")
        return

    await update.message.reply_text(_format_ticket(ticket), parse_mode="Markdown")


async def resolve_ticket_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text("This command is restricted to admins.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /resolve_ticket <ticket_id> [note]")
        return

    try:
        ticket_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Ticket ID must be a number.")
        return

    note = " ".join(context.args[1:]).strip() or "Resolved by admin"
    ticket = session_store.update_support_ticket(
        ticket_id,
        status="resolved",
        resolution_note=note,
        assigned_to=update.effective_user.username or update.effective_user.full_name,
    )
    if not ticket:
        await update.message.reply_text(f"Ticket #{ticket_id} not found.")
        return

    await update.message.reply_text(f"Ticket #{ticket_id} marked as resolved.")
