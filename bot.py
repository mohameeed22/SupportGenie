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
from handlers.order_tracking import (
    ask_for_order_id,
    handle_order_id,
    cancel_tracking,
    WAITING_FOR_ORDER_ID,
)

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

    reply = await get_ai_response(user_id, user_text)
    await update.message.reply_text(reply, parse_mode="Markdown")


# ── Bot Setup ─────────────────────────────────────────────────────────────────
def main() -> None:
    config.validate_config()

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

    # ── Register handlers (order matters!) ────────────────────────────────────
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(order_conv)
    app.add_handler(CallbackQueryHandler(menu_router))  # all other buttons
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_message_handler))

    # ── Start ─────────────────────────────────────────────────────────────────
    logger.info("SupportGenie Bot is starting...")
    logger.info("AI Model: %s", config.GROQ_MODEL)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
