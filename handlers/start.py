"""
handlers/start.py — /start and /help commands.

Sends a branded welcome message with the main inline keyboard menu.
"""

from telegram import Update
from telegram.ext import ContextTypes

import ai_handler
from handlers.menu import main_menu_keyboard

WELCOME_TEXT = """
👋 Welcome to **SupportGenie**! ✨

I'm **Genie**, your AI-powered store assistant. I can help you with:

• 📦 Tracking your order
• 🔎 Searching products by keyword
• ↩️ Starting a return / refund request
• ❓ Answering product & policy questions
• 🧑‍💼 Connecting you with our team

Just type your question, or use the menu below to get started!
""".strip()


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — reset history and show welcome message."""
    user_id = update.effective_user.id
    ai_handler.clear_history(user_id)

    await update.message.reply_text(
        WELCOME_TEXT,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help — same as /start."""
    await start_handler(update, context)
