"""
handlers/menu.py — Central dispatcher for all inline keyboard button presses.

Routes callback_data to the appropriate handler.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.faq import show_faq_menu, show_faq_answer, FAQS
from handlers.fallback import human_escalation, products_overview
from handlers.order_tracking import ask_for_order_id
from handlers.product_search import ask_for_search_query
from handlers.returns import ask_for_return_order_id


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📦 Track My Order", callback_data="menu:track"),
            InlineKeyboardButton("🔎 Search Products", callback_data="menu:search"),
        ],
        [
            InlineKeyboardButton("❓ FAQs", callback_data="menu:faq"),
            InlineKeyboardButton("↩️ Returns", callback_data="menu:returns"),
        ],
        [
            InlineKeyboardButton("🛍️ Our Products", callback_data="menu:products"),
            InlineKeyboardButton("🧑‍💼 Talk to a Human", callback_data="menu:human"),
        ],
    ])


async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route all callback_query events to the right handler."""
    query = update.callback_query
    data = query.data

    # ── Main menu sections ────────────────────────────────────────────────────
    if data == "menu:main":
        await query.answer()
        await query.edit_message_text(
            "👋 What can I help you with?\n\nChoose an option below or just type your question:",
            reply_markup=main_menu_keyboard(),
        )

    elif data == "menu:faq":
        await show_faq_menu(update, context)

    elif data == "menu:search":
        await ask_for_search_query(update, context)

    elif data == "menu:track":
        # Hand off to ConversationHandler — ask_for_order_id will handle the edit
        await ask_for_order_id(update, context)

    elif data == "menu:returns":
        await ask_for_return_order_id(update, context)

    elif data == "menu:human":
        await human_escalation(update, context)

    elif data == "menu:products":
        await products_overview(update, context)

    # ── FAQ answers ───────────────────────────────────────────────────────────
    elif data in FAQS:
        await show_faq_answer(update, context)

    else:
        await query.answer("Unknown option. Please try again.", show_alert=True)
