from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)


def _back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🏠 Back to Menu", callback_data="menu:main")]]
    )


async def products_overview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        reply_markup=_back_menu(),
    )
