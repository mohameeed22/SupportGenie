"""Return and refund conversation flow."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from db import session_store
from feedback import feedback_keyboard
from handlers.order_tracking import lookup_order, normalize_order_id

WAITING_FOR_RETURN_ORDER_ID = 1
WAITING_FOR_RETURN_REASON = 2


def _back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🏠 Main Menu", callback_data="menu:main"),
                InlineKeyboardButton("❓ FAQs", callback_data="menu:faq"),
            ]
        ]
    )


async def ask_for_return_order_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "↩️ *Return / Refund Request*\n\nPlease enter your Order ID.",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            "↩️ *Return / Refund Request*\n\nPlease enter your Order ID.",
            parse_mode="Markdown",
        )
    return WAITING_FOR_RETURN_ORDER_ID


async def handle_return_order_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_id = normalize_order_id(update.message.text)
    order = lookup_order(order_id)
    context.user_data["return_order_id"] = order_id

    if not order:
        await update.message.reply_text(
            f"❌ I couldn't find *{order_id}*.\nPlease double-check the ID and try again.",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    if order["status"] != "Delivered":
        await update.message.reply_text(
            f"⚠️ *{order_id}* is marked as *{order['status']}*.\n"
            "Returns are usually only available after delivery.",
            parse_mode="Markdown",
            reply_markup=_back_keyboard(),
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Please briefly describe why you want the return (defect, change of mind, wrong item, etc.)."
    )
    return WAITING_FOR_RETURN_REASON


async def handle_return_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    order_id = context.user_data.get("return_order_id", "your order")
    reason = update.message.text.strip()
    session_store.record_event(
        user.id,
        "return_request",
        question=order_id,
        details={"reason": reason},
    )

    await update.message.reply_text(
        f"✅ Thanks — I’ve noted your return request for *{order_id}*.\n\n"
        "• Returns are available within 30 days of delivery\n"
        "• Electronics must be unopened/unused for a full refund\n"
        "• Defective items qualify for free return shipping\n\n"
        "Please email support with your Order ID to finalize the return.",
        parse_mode="Markdown",
        reply_markup=feedback_keyboard(source="returns"),
    )
    context.user_data.pop("return_order_id", None)
    return ConversationHandler.END


async def cancel_returns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Return flow cancelled.")
    context.user_data.pop("return_order_id", None)
    return ConversationHandler.END
