from telegram import Update
from telegram.ext import ContextTypes

from ai_handler import clear_history


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    clear_history(user_id)
    await update.message.reply_text("🧹 Conversation cleared! You can start fresh.")
