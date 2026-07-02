"""
bot.py — NovaBuy Customer Support Bot
Entry point. Registers all handlers and starts polling.

Usage:
    python bot.py

Requirements:
    Copy .env.example to .env and fill in your tokens.
"""

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

import config
from ai_handler import get_ai_response
from handlers.start import start_handler, help_handler
from handlers.menu import menu_router
from handlers.product_search import (
    ask_for_search_query,
    handle_search_query,
    cancel_search,
    WAITING_FOR_SEARCH_QUERY,
)
from handlers.returns import (
    ask_for_return_order_id,
    handle_return_order_id,
    handle_return_reason,
    cancel_returns,
    WAITING_FOR_RETURN_ORDER_ID,
    WAITING_FOR_RETURN_REASON,
)
from handlers.order_tracking import (
    ask_for_order_id,
    handle_order_id,
    cancel_tracking,
    WAITING_FOR_ORDER_ID,
)
from feedback import handle_feedback, feedback_keyboard
from handlers.admin import stats_command, broadcast_command
from handlers.sentiment import analyze_sentiment
from db import session_store
from handlers.fallback import human_escalation

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# ── AI Free-text Handler ──────────────────────────────────────────────────────
async def ai_message_handler(update: Update, context) -> None:
    """
    Handle any plain text message that isn't a command.
    Sends a typing indicator, then streams the AI response.
    """
    user_id = update.effective_user.id
    user_text = update.message.text

    # Show typing indicator while AI thinks
    await update.message.chat.send_action("typing")

    session_store.upsert_user(
        user_id,
        username=update.effective_user.username,
        full_name=update.effective_user.full_name,
    )

    sentiment = analyze_sentiment(user_text)
    if sentiment.escalate:
        session_store.record_escalation(
            user_id, reason="sentiment-trigger", source="ai-chat"
        )
        await human_escalation(update, context)
        return

    placeholder = await update.message.reply_text("Thinking...")

    reply = await get_ai_response(user_id, user_text, stream_message=placeholder)
    await placeholder.edit_text(reply, reply_markup=feedback_keyboard(source="ai-chat"))


# ── Bot Setup ─────────────────────────────────────────────────────────────────
def main() -> None:
    config.validate_config()

    # Initialize database
    session_store.initialize()
    logger.info("Database initialized: %s", session_store.DB_PATH)

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # ── Order tracking conversation ───────────────────────────────────────────
    # This must be registered BEFORE the generic CallbackQueryHandler
    order_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(ask_for_order_id, pattern="^menu:track$"),
        ],
        states={
            WAITING_FOR_ORDER_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order_id),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_tracking),
            CommandHandler("start", start_handler),
        ],
        per_user=True,
        per_chat=True,
        per_message=False,
    )

    search_conv = ConversationHandler(
        entry_points=[
            CommandHandler("search", ask_for_search_query),
            CallbackQueryHandler(ask_for_search_query, pattern="^menu:search$"),
        ],
        states={
            WAITING_FOR_SEARCH_QUERY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_query),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_search),
            CommandHandler("start", start_handler),
        ],
        per_user=True,
        per_chat=True,
        per_message=False,
    )

    returns_conv = ConversationHandler(
        entry_points=[
            CommandHandler("returns", ask_for_return_order_id),
            CallbackQueryHandler(ask_for_return_order_id, pattern="^menu:returns$"),
        ],
        states={
            WAITING_FOR_RETURN_ORDER_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_return_order_id),
            ],
            WAITING_FOR_RETURN_REASON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_return_reason),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_returns),
            CommandHandler("start", start_handler),
        ],
        per_user=True,
        per_chat=True,
        per_message=False,
    )

    # ── Register handlers (order matters!) ────────────────────────────────────
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(order_conv)
    app.add_handler(search_conv)
    app.add_handler(returns_conv)
    app.add_handler(CallbackQueryHandler(menu_router))  # all other buttons
    app.add_handler(CallbackQueryHandler(handle_feedback, pattern="^feedback:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_message_handler))

    # ── Start ─────────────────────────────────────────────────────────────────
    logger.info("SupportGenie Bot is starting...")
    logger.info("AI Model: %s", config.GROQ_MODEL)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
