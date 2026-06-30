"""
handlers/start.py — /start and /help commands.

Sends a branded welcome message with the main inline keyboard menu.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import ai_handler

WELCOME_TEXT = """
👋 Welcome to **SupportGenie**! ✨

I'm **Genie**, your AI-powered store assistant. I can help you with:

• 📦 Tracking your order
• ❓ Answering product & policy questions
• 🛍️ Finding the right product for you
• 🧑‍💼 Connecting you with our team

Just type your question, or use the menu below to get started!
""".strip()


def _main_menu() -> InlineKeyboardMarkup:
    """Returns the main inline keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📦 Track My Order", callback_data="menu:track"),
            InlineKeyboardButton("❓ FAQs", callback_data="menu:faq"),
        ],
        [
            InlineKeyboardButton("🛍️ Our Products", callback_data="menu:products"),
            InlineKeyboardButton("🧑‍💼 Talk to a Human", callback_data="menu:human"),
        ],
    ])


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — reset history and show welcome message."""
    user_id = update.effective_user.id
    ai_handler.clear_history(user_id)

    await update.message.reply_text(
        WELCOME_TEXT,
        parse_mode="Markdown",
        reply_markup=_main_menu(),
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help — same as /start."""
    await start_handler(update, context)
