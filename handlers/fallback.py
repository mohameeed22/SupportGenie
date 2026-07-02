"""
handlers/fallback.py — Human escalation and out-of-scope handler.
"""

import config
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)


def _back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🏠 Back to Menu", callback_data="menu:main")]]
    )


async def human_escalation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Triggered by 'Talk to a Human' button OR called programmatically
    when AI detects it cannot help. Works for both messages and callback queries.
    """
    text = (
        "🧑‍💼 *Connecting you with our support team*\n\n"
        f"📧 Email: *{config.SUPPORT_EMAIL}*\n"
        f"🕐 Hours: {config.SUPPORT_HOURS}\n"
        f"⚡ Response time: Within 4 hours\n\n"
        "Please include your *Order ID* and a description of your issue for faster service.\n\n"
        "_In the meantime, our FAQ section may have the answer you need!_ 👇"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("❓ Browse FAQs", callback_data="menu:faq")],
            [InlineKeyboardButton("🏠 Back to Menu", callback_data="menu:main")],
        ]
    )

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.chat.send_action("typing")
        await query.edit_message_text(
            text, parse_mode="Markdown", reply_markup=keyboard
        )
    else:
        await update.message.chat.send_action("typing")
        await update.message.reply_text(
            text, parse_mode="Markdown", reply_markup=keyboard
        )

    # Log the escalation for monitoring
    user = update.effective_user
    logger.info(
        "ESCALATION — User %s (@%s, ID: %s) requested human support.",
        user.full_name,
        user.username,
        user.id,
    )


async def products_overview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show a quick product catalog overview."""
    from store_context import PRODUCTS

    query = update.callback_query
    await query.answer()
    await query.message.chat.send_action("typing")

    in_stock = [p for p in PRODUCTS if p["in_stock"]]
    out_of_stock = [p for p in PRODUCTS if not p["in_stock"]]

    lines = ["🛍️ *NovaBuy Product Catalog*\n"]
    for p in in_stock:
        lines.append(f"✅ *{p['name']}* — ${p['price']:.2f}")
    for p in out_of_stock:
        lines.append(f"❌ *{p['name']}* — ${p['price']:.2f} _(Out of Stock)_")

    lines.append("\n_Just ask me anything about a product for more details!_")

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🏠 Back to Menu", callback_data="menu:main")]]
        ),
    )
