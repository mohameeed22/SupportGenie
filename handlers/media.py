from __future__ import annotations

import io
import logging
import tempfile
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

import config
from ai_handler import get_ai_response
from db import session_store
from feedback import feedback_keyboard

logger = logging.getLogger(__name__)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not update.message.photo:
        return

    session_store.upsert_user(user.id, username=user.username, full_name=user.full_name)

    photo = update.message.photo[-1]
    caption = update.message.caption or "What is this product?"

    await update.message.chat.send_action("typing")

    try:
        file = await photo.get_file()
        photo_bytes = io.BytesIO()
        await file.download_to_memory(photo_bytes)
        photo_bytes.seek(0)

        import base64

        b64 = base64.b64encode(photo_bytes.read()).decode("utf-8")

        from groq import AsyncGroq

        groq = AsyncGroq(api_key=config.GROQ_API_KEY)

        vision_prompt = (
            f"The user sent an image with this caption: '{caption}'. "
            "Describe what you see and answer any question in the caption. "
            "If it looks like a product, identify it and relate it to NovaBuy's catalog."
        )

        response = await groq.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": vision_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64}"
                            },
                        },
                    ],
                }
            ],
            temperature=0.3,
            max_tokens=1024,
        )

        reply = response.choices[0].message.content or "I couldn't process that image."
        await update.message.reply_text(reply, reply_markup=feedback_keyboard(source="image"))

        session_store.record_event(
            user.id,
            "image_query",
            question=caption,
            answer=reply,
        )
    except Exception as exc:
        logger.exception("Image processing failed")
        await update.message.reply_text(
            "I couldn't process that image right now. Try sending a text description instead!"
        )


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not update.message.voice:
        return

    session_store.upsert_user(user.id, username=user.username, full_name=user.full_name)

    voice = update.message.voice
    await update.message.chat.send_action("typing")

    try:
        file = await voice.get_file()
        voice_bytes = io.BytesIO()
        await file.download_to_memory(voice_bytes)
        voice_bytes.seek(0)

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp.write(voice_bytes.read())
            tmp_path = tmp.name

        from groq import AsyncGroq

        groq = AsyncGroq(api_key=config.GROQ_API_KEY)

        with open(tmp_path, "rb") as f:
            transcription = await groq.audio.transcriptions.create(
                file=(Path(tmp_path).name, f.read()),
                model="whisper-large-v3",
                response_format="text",
            )

        Path(tmp_path).unlink(missing_ok=True)

        text = transcription.strip() if isinstance(transcription, str) else (transcription.text or "")
        if not text:
            await update.message.reply_text("I couldn't understand the audio. Please try again or type your message.")
            return

        placeholder = await update.message.reply_text(f'🎤 Heard: "{text}"\n\nThinking...')
        reply = await get_ai_response(user.id, text, stream_message=placeholder)
        await placeholder.edit_text(reply, reply_markup=feedback_keyboard(source="voice"))

        session_store.record_event(
            user.id,
            "voice_query",
            question=text,
            answer=reply,
        )
    except Exception as exc:
        logger.exception("Voice processing failed")
        await update.message.reply_text(
            "I couldn't process that voice message. Please try typing instead!"
        )
