"""
handlers/faq.py — Static FAQ answers with inline navigation.

Using static (non-AI) responses here keeps FAQs instant, free, and reliable.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# ── FAQ Data ──────────────────────────────────────────────────────────────────
FAQS: dict[str, dict] = {
    "faq:returns": {
        "question": "What is your return policy?",
        "answer": (
            "🔄 *Return Policy*\n\n"
            "• 30-day hassle-free returns from delivery date\n"
            "• Items must be in original condition & packaging\n"
            "• Electronics: *unopened* = full refund; opened = exchange or store credit\n"
            "• To start a return, email *support@novabuy.store* with your Order ID\n"
            "• Refunds processed in 5–7 business days\n"
            "• Return shipping: FREE for defects, $4.99 for change of mind"
        ),
    },
    "faq:shipping": {
        "question": "How long does shipping take?",
        "answer": (
            "🚚 *Shipping Times*\n\n"
            "• Standard: 3–5 business days — FREE over $50, else $5.99\n"
            "• Express: 1–2 business days — $12.99\n"
            "• Same-day: Select cities, orders before 12pm — $19.99\n"
            "• International: 7–14 business days, 40+ countries\n\n"
            "Orders are processed within 1 business day and you'll receive a tracking email once shipped."
        ),
    },
    "faq:payment": {
        "question": "What payment methods do you accept?",
        "answer": (
            "💳 *Payment Methods*\n\n"
            "• Visa, Mastercard, Amex, Discover\n"
            "• PayPal, Apple Pay, Google Pay\n"
            "• Shop Pay (4 interest-free installments)\n\n"
            "All transactions are protected with 256-bit SSL encryption. 🔒"
        ),
    },
    "faq:international": {
        "question": "Do you ship internationally?",
        "answer": (
            "🌍 *International Shipping*\n\n"
            "Yes! We ship to 40+ countries worldwide.\n\n"
            "• Delivery time: 7–14 business days\n"
            "• Shipping cost: Calculated at checkout based on destination\n"
            "• Customs & import duties may apply and are the buyer's responsibility\n\n"
            "If your country is not available at checkout, contact us at *support@novabuy.store*."
        ),
    },
    "faq:cancel": {
        "question": "How do I cancel my order?",
        "answer": (
            "❌ *Order Cancellations*\n\n"
            "• You can cancel within *1 hour* of placing your order for a full refund\n"
            "• After 1 hour (if not yet shipped): contact *support@novabuy.store* and we'll do our best\n"
            "• Once shipped: cancellation is not possible, but our 30-day return policy applies\n\n"
            "Always include your Order ID (NB-XXXXX) when contacting support."
        ),
    },
    "faq:warranty": {
        "question": "What warranty do products come with?",
        "answer": (
            "🛡️ *Warranty*\n\n"
            "All NovaBuy products include a *12-month manufacturer warranty* against defects.\n\n"
            "• Extended plans (2 or 3 years) available at checkout\n"
            "• Warranty covers manufacturing defects, not accidental damage\n"
            "• To make a warranty claim: email *support@novabuy.store* with your Order ID and a description of the issue"
        ),
    },
}


def _faq_menu() -> InlineKeyboardMarkup:
    """Inline keyboard listing all FAQ topics."""
    buttons = [
        [InlineKeyboardButton(f"• {data['question']}", callback_data=key)]
        for key, data in FAQS.items()
    ]
    buttons.append([InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu:main")])
    return InlineKeyboardMarkup(buttons)


def _back_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⬅️ More FAQs", callback_data="menu:faq"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu:main"),
        ]
    ])


async def show_faq_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the FAQ topic list."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "❓ *Frequently Asked Questions*\n\nSelect a topic below:",
        parse_mode="Markdown",
        reply_markup=_faq_menu(),
    )


async def show_faq_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the answer to a selected FAQ."""
    query = update.callback_query
    await query.answer()

    faq_key = query.data
    faq = FAQS.get(faq_key)

    if not faq:
        await query.edit_message_text("Sorry, I couldn't find that answer. Please try again.")
        return

    await query.edit_message_text(
        faq["answer"],
        parse_mode="Markdown",
        reply_markup=_back_button(),
    )
