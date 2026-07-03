"""config.py — Loads and validates environment variables."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, field_validator

load_dotenv()

# ── Telegram ──────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

# ── Groq AI ───────────────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ── Support Info ──────────────────────────────────────────────────────────────
SUPPORT_EMAIL: str = os.getenv("SUPPORT_EMAIL", "support@novabuy.store")
SUPPORT_HOURS: str = os.getenv("SUPPORT_HOURS", "Monday-Friday, 9am-6pm EST")

# ── Operational Settings ──────────────────────────────────────────────────────
ADMIN_USER_IDS: set[int] = set()
_raw_admin_ids = os.getenv("ADMIN_USER_IDS", "")
if _raw_admin_ids.strip():
    ADMIN_USER_IDS = {
        int(item.strip()) for item in _raw_admin_ids.split(",") if item.strip()
    }

# Optional live integrations
ORDER_LOOKUP_URL: str = os.getenv("ORDER_LOOKUP_URL", "")
ORDER_LOOKUP_API_KEY: str = os.getenv("ORDER_LOOKUP_API_KEY", "")
ORDER_LOOKUP_TIMEOUT_SECONDS: float = float(
    os.getenv("ORDER_LOOKUP_TIMEOUT_SECONDS", "5")
)

RATE_LIMIT_MAX_MESSAGES: int = int(os.getenv("RATE_LIMIT_MAX_MESSAGES", "10"))
RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
DB_PATH: str = os.getenv("SUPPORTGENIE_DB_PATH", "supportgenie.db")


class Settings(BaseModel):
    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    groq_api_key: str = Field(alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")
    support_email: str = Field(default="support@novabuy.store", alias="SUPPORT_EMAIL")
    support_hours: str = Field(
        default="Monday-Friday, 9am-6pm EST", alias="SUPPORT_HOURS"
    )
    admin_user_ids: set[int] = Field(default_factory=set, alias="ADMIN_USER_IDS")
    order_lookup_url: str = Field(default="", alias="ORDER_LOOKUP_URL")
    order_lookup_api_key: str = Field(default="", alias="ORDER_LOOKUP_API_KEY")
    order_lookup_timeout_seconds: float = Field(
        default=5, alias="ORDER_LOOKUP_TIMEOUT_SECONDS", gt=0
    )
    rate_limit_max_messages: int = Field(
        default=10, alias="RATE_LIMIT_MAX_MESSAGES", ge=1
    )
    rate_limit_window_seconds: int = Field(
        default=60, alias="RATE_LIMIT_WINDOW_SECONDS", ge=10
    )
    db_path: str = Field(default="supportgenie.db", alias="SUPPORTGENIE_DB_PATH")

    @field_validator("admin_user_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, value: Any) -> set[int]:
        if value in (None, ""):
            return set()
        if isinstance(value, str):
            return {int(item.strip()) for item in value.split(",") if item.strip()}
        if isinstance(value, (list, tuple, set)):
            return {int(item) for item in value}
        return value


def validate_config() -> None:
    """Raise EnvironmentError if required variables are missing or invalid."""
    try:
        Settings.model_validate(os.environ)
    except ValidationError as exc:
        raise EnvironmentError(f"Invalid environment configuration:\n{exc}") from exc
