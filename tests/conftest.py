"""Pytest configuration and shared fixtures."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    if Path(db_path).exists():
        Path(db_path).unlink()
    wal = Path(db_path + "-wal")
    if wal.exists():
        wal.unlink()
    shm = Path(db_path + "-shm")
    if shm.exists():
        shm.unlink()


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Set required environment variables for tests."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token-123")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    monkeypatch.setenv("SUPPORTGENIE_DB_PATH", ":memory:")


@pytest.fixture
def test_user_id():
    """Standard test user ID."""
    return 123456789


@pytest.fixture
def test_user_data():
    """Standard test user data."""
    return {
        "username": "testuser",
        "full_name": "Test User",
        "preferred_language": "English",
    }
