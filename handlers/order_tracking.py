"""
handlers/order_tracking.py — Multi-step order lookup flow using ConversationHandler.

Flow:
  1. User taps "Track My Order" -> bot asks for Order ID
  2. User sends Order ID -> bot looks up mock_orders.json and returns status
"""

import json
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

logger = logging.getLogger(__name__)

# Conversation state
WAITING_FOR_ORDER_ID = 1

# Path to mock orders
_ORDERS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "mock_orders.json")

# Load orders into memory once at startup
def _load_orders() -> dict[str, dict]:
    try:
        with open(_ORDERS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {order["order_id"]: order for order in data["orders"]}
    except Exception as e:
        logger.error("Failed to load mock_orders.json: %s", e)
        return {}

ORDERS: dict[str, dict] = _load_orders()


def _back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📦 Track Another", callback_data="menu:track"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu:main"),
        ]
    ])


def _format_order(order: dict) -> str:
    """Format an order dict into a readable Telegram message."""
    status = order["status"]
    status_emoji = {
        "Processing": "⏳",
        "Shipped": "🚚",
        "Delivered": "✅",
        "Cancelled": "❌",
    }.get(status, "📦")

    lines = [
        f"*Order {order['order_id']}*",
        f"{status_emoji} Status: *{status}*",
        f"",
        f"📋 Item: {order['item']}",
        f"💰 Total: ${order['total']:.2f}",
        f"📅 Order Date: {order['order_date']}",
    ]

    if status == "Shipped":
        lines += [
            f"",
            f"🚛 Carrier: {order.get('carrier', 'N/A')}",
            f"🔍 Tracking: `{order.get('tracking_number', 'N/A')}`",
            f"📆 Est. Delivery: {order.get('estimated_delivery', 'N/A')}",
        ]
    elif status == "Delivered":
        lines += [
            f"",
            f"🎉 Delivered on: {order.get('delivered_date', 'N/A')}",
            f"🛡️ 30-day returns available if needed.",
        ]
    elif status == "Processing":
        lines += [
            f"",
            f"⏱️ Your order is being prepared. Est. dispatch: within 1 business day.",
            f"📆 Est. Delivery: {order.get('estimated_delivery', 'N/A')}",
        ]
    elif status == "Cancelled":
        lines += [
            f"",
            f"ℹ️ Reason: {order.get('cancel_reason', 'N/A')}",
            f"💵 Refund: {order.get('refund_status', 'N/A')}",
        ]

    return "\n".join(lines)


async def ask_for_order_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Triggered by inline button — ask the user for their order ID."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📦 *Order Tracker*\n\n"
        "Please enter your Order ID below.\n"
        "_It looks like this: *NB-10042*_\n\n"
        "You can find it in your confirmation email.",
        parse_mode="Markdown",
    )
    return WAITING_FOR_ORDER_ID


async def handle_order_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive the order ID and look it up."""
    raw = update.message.text.strip().upper()

    # Normalize: accept "10042" or "NB10042" or "NB-10042"
    if not raw.startswith("NB-"):
        if raw.startswith("NB"):
            raw = "NB-" + raw[2:]
        elif raw.isdigit():
            raw = "NB-" + raw

    order = ORDERS.get(raw)

    if order:
        await update.message.reply_text(
            _format_order(order),
            parse_mode="Markdown",
            reply_markup=_back_menu(),
        )
    else:
        await update.message.reply_text(
            f"❌ I couldn't find an order with ID *{raw}*.\n\n"
            "Please double-check and try again, or contact our support team.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📦 Try Again", callback_data="menu:track")],
                [InlineKeyboardButton("🧑‍💼 Talk to a Human", callback_data="menu:human")],
            ]),
        )

    return ConversationHandler.END


async def cancel_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the order tracking conversation."""
    await update.message.reply_text("Order tracking cancelled. How else can I help?")
    return ConversationHandler.END
