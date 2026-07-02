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
        "context": "Return policy: 30-day hassle-free returns, unopened electronics qualify for full refund, opened electronics qualify for exchange or store credit, defective items get free return shipping.",
    },
    "faq:shipping": {
        "question": "How long does shipping take?",
        "context": "Shipping policy: standard 3-5 business days, express 1-2 business days, same-day in select cities before 12pm, international 7-14 business days.",
    },
    "faq:payment": {
        "question": "What payment methods do you accept?",
        "context": "Payment methods: Visa, Mastercard, Amex, Discover, PayPal, Apple Pay, Google Pay, and Shop Pay in 4 installments.",
    },
    "faq:international": {
        "question": "Do you ship internationally?",
        "context": "International shipping is available to 40+ countries and usually takes 7-14 business days.",
    },
    "faq:cancel": {
        "question": "How do I cancel my order?",
        "context": "Orders can be cancelled within 1 hour for a full refund; after that, support may still help if it has not shipped.",
    },
    "faq:warranty": {
        "question": "What warranty do products come with?",
        "context": "Warranty: all products include a 12-month manufacturer warranty against defects; extended plans are available at checkout.",
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
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⬅️ More FAQs", callback_data="menu:faq"),
                InlineKeyboardButton("🏠 Main Menu", callback_data="menu:main"),
            ]
        ]
    )


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
        await query.edit_message_text(
            "Sorry, I couldn't find that answer. Please try again."
        )
        return

    from ai_handler import get_ai_response

    await query.message.chat.send_action("typing")
    answer = await get_ai_response(
        update.effective_user.id,
        faq["question"],
        extra_context=faq["context"],
    )
    await query.edit_message_text(
        answer,
        reply_markup=_back_button(),
    )
