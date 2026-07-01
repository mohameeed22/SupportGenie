"""Keyword-based product search."""

from __future__ import annotations

from collections import Counter

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from db import session_store
from feedback import feedback_keyboard
from store_context import PRODUCTS

WAITING_FOR_SEARCH_QUERY = 1


def _search_products(query: str, limit: int = 5) -> list[dict]:
    tokens = [token for token in query.lower().split() if token]
    if not tokens:
        return []

    ranked: list[tuple[int, dict]] = []
    for product in PRODUCTS:
        haystack = " ".join(
            [
                product["name"],
                product["category"],
                product["description"],
            ]
        ).lower()
        score = 0
        for token in tokens:
            if token in product["name"].lower():
                score += 5
            if token in product["category"].lower():
                score += 3
            if token in haystack:
                score += 1
        ranked.append((score, product))

    ranked.sort(key=lambda item: (item[0], item[1]["in_stock"]), reverse=True)
    return [product for score, product in ranked if score > 0][:limit]


def format_search_results(query: str, products: list[dict]) -> str:
    if not products:
        return (
            f"🔎 I couldn't find a close match for *{query}*.\n\n"
            "Try a broader keyword like `mouse`, `charger`, or `keyboard`."
        )

    lines = [f"🔎 *Search results for {query}*"]
    for product in products:
        stock = "In stock" if product["in_stock"] else "Out of stock"
        lines.append(
            f"\n• *{product['name']}* — ${product['price']:.2f}\n"
            f"  {stock} · {product['category']}\n"
            f"  {product['description']}"
        )
    return "\n".join(lines)


def _back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🏠 Main Menu", callback_data="menu:main")],
        ]
    )


async def ask_for_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and context.args:
        query = " ".join(context.args).strip()
        await handle_search_query_text(update, context, query)
        return ConversationHandler.END

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "🔎 *Product Search*\n\nType a keyword like `wireless mouse` or `charger`.",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            "🔎 *Product Search*\n\nType a keyword like `wireless mouse` or `charger`.",
            parse_mode="Markdown",
        )
    return WAITING_FOR_SEARCH_QUERY


async def handle_search_query_text(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    user = update.effective_user
    session_store.upsert_user(
        user.id,
        username=user.username,
        full_name=user.full_name,
    )
    session_store.record_event(user.id, "search", question=query)
    results = _search_products(query)
    await update.message.reply_text(
        format_search_results(query, results),
        parse_mode="Markdown",
        reply_markup=feedback_keyboard(source="product-search"),
    )


async def handle_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    await handle_search_query_text(update, context, query)
    return ConversationHandler.END


async def cancel_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Product search cancelled.")
    return ConversationHandler.END

