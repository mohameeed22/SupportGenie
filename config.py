"""
config.py — Loads and validates all environment variables.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ──────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

# ── Groq AI ───────────────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ── Support Info ──────────────────────────────────────────────────────────────
SUPPORT_EMAIL: str = os.getenv("SUPPORT_EMAIL", "support@novabuy.store")
SUPPORT_HOURS: str = os.getenv("SUPPORT_HOURS", "Monday-Friday, 9am-6pm EST")


def validate_config() -> None:
    """Raise EnvironmentError if any required variables are missing."""
    errors = []
    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN is not set.")
    if not GROQ_API_KEY:
        errors.append("GROQ_API_KEY is not set.")
    if errors:
        raise EnvironmentError(
            "Missing required environment variables:\n"
            + "\n".join(f"  • {e}" for e in errors)
        )
