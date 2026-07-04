"""
bot.py — NovaBuy Customer Support Bot
Entry point. Registers all handlers and starts polling or webhook.
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
from handlers.media import handle_photo, handle_voice
from handlers.handoff import human_escalation, forward_from_support_group
from handlers.clear import clear_command
from handlers.csat import handle_csat
from feedback import handle_feedback, feedback_keyboard
from handlers.admin import (
    stats_command,
    broadcast_command,
    inbox_command,
    ticket_command,
    resolve_ticket_command,
    feedback_command,
)
from handlers.sentiment import analyze_sentiment
from db import session_store

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s \u2014 %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def ai_message_handler(update: Update, context) -> None:
    user_id = update.effective_user.id
    user_text = update.message.text

    await update.message.chat.send_action("typing")

    session_store.upsert_user(
        user_id,
        username=update.effective_user.username,
        full_name=update.effective_user.full_name,
    )

    if session_store.user_message_rate_limited(user_id):
        await update.message.reply_text(
            "⏳ You're sending messages too fast. Please slow down and try again in a moment."
        )
        return

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


async def csat_handler(update: Update, context) -> None:
    await handle_csat(update, context)


async def error_handler(update: Update, context) -> None:
    logger.exception("Unhandled error: %s", context.error)


async def post_init(application: Application) -> None:
    if config.WEBHOOK_URL:
        webhook_url = config.WEBHOOK_URL.rstrip("/") + "/webhook"
        await application.bot.set_webhook(url=webhook_url)
        logger.info("Webhook set to %s", webhook_url)

    if config.NOTIFICATION_CHECK_INTERVAL > 0:
        job_queue = application.job_queue
        if job_queue:
            job_queue.run_repeating(
                check_order_updates,
                interval=config.NOTIFICATION_CHECK_INTERVAL * 60,
                first=config.NOTIFICATION_CHECK_INTERVAL * 60,
            )
            logger.info("Notification check scheduled every %d minutes", config.NOTIFICATION_CHECK_INTERVAL)


async def check_order_updates(context) -> None:
    logger.debug("Order update check running...")


def main() -> None:
    config.validate_config()

    session_store.initialize()
    logger.info("Database initialized: %s", session_store.DB_PATH)

    app = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

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

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("feedback", feedback_command))
    app.add_handler(CommandHandler("inbox", inbox_command))
    app.add_handler(CommandHandler("ticket", ticket_command))
    app.add_handler(CommandHandler("resolve_ticket", resolve_ticket_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(order_conv)
    app.add_handler(search_conv)
    app.add_handler(returns_conv)
    app.add_handler(CallbackQueryHandler(menu_router))
    app.add_handler(CallbackQueryHandler(handle_feedback, pattern="^feedback:"))
    app.add_handler(CallbackQueryHandler(csat_handler, pattern="^csat:"))

    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    if config.SUPPORT_GROUP_CHAT_ID:
        app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & filters.Chat(chat_id=config.SUPPORT_GROUP_CHAT_ID),
                forward_from_support_group,
            )
        )

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_message_handler))

    app.add_error_handler(error_handler)

    logger.info("SupportGenie Bot starting...")
    logger.info("AI Model: %s", config.GROQ_MODEL)

    if config.WEBHOOK_URL:
        logger.info("Mode: Webhook on port %d", config.WEBHOOK_PORT)
        app.run_webhook(
            listen="0.0.0.0",
            port=config.WEBHOOK_PORT,
            webhook_url="/webhook",
            secret_token=config.TELEGRAM_BOT_TOKEN,
        )
    else:
        logger.info("Mode: Polling")
        app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
