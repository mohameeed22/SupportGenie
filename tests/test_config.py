"""Tests for configuration and environment validation."""

import os
import pytest
from pydantic import ValidationError
from config import Settings, validate_config


class TestConfigValidation:
    def test_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            Settings.model_validate({})
    
    def test_valid_config(self):
        """Test valid configuration."""
        config = Settings.model_validate({
            "TELEGRAM_BOT_TOKEN": "test-token",
            "GROQ_API_KEY": "test-key",
        })
        assert config.telegram_bot_token == "test-token"
        assert config.groq_api_key == "test-key"
    
    def test_default_values(self):
        """Test default values are applied."""
        config = Settings.model_validate({
            "TELEGRAM_BOT_TOKEN": "test",
            "GROQ_API_KEY": "test",
        })
        assert config.groq_model == "llama-3.3-70b-versatile"
        assert config.rate_limit_max_messages == 10
        assert config.rate_limit_window_seconds == 60
    
    def test_admin_ids_parsing_string(self):
        """Test ADMIN_USER_IDS parsing from comma-separated string."""
        config = Settings.model_validate({
            "TELEGRAM_BOT_TOKEN": "test",
            "GROQ_API_KEY": "test",
            "ADMIN_USER_IDS": "123,456,789",
        })
        assert config.admin_user_ids == {123, 456, 789}
    
    def test_admin_ids_parsing_empty(self):
        """Test ADMIN_USER_IDS parsing empty string."""
        config = Settings.model_validate({
            "TELEGRAM_BOT_TOKEN": "test",
            "GROQ_API_KEY": "test",
            "ADMIN_USER_IDS": "",
        })
        assert config.admin_user_ids == set()
    
    def test_admin_ids_parsing_list(self):
        """Test ADMIN_USER_IDS parsing from list."""
        config = Settings.model_validate({
            "TELEGRAM_BOT_TOKEN": "test",
            "GROQ_API_KEY": "test",
            "ADMIN_USER_IDS": [123, 456],
        })
        assert config.admin_user_ids == {123, 456}
    
    def test_rate_limit_constraints(self):
        """Test rate limit field constraints."""
        with pytest.raises(ValidationError):
            Settings.model_validate({
                "TELEGRAM_BOT_TOKEN": "test",
                "GROQ_API_KEY": "test",
                "RATE_LIMIT_MAX_MESSAGES": 0,  # Must be >= 1
            })
        
        with pytest.raises(ValidationError):
            Settings.model_validate({
                "TELEGRAM_BOT_TOKEN": "test",
                "GROQ_API_KEY": "test",
                "RATE_LIMIT_WINDOW_SECONDS": 5,  # Must be >= 10
            })
    
    def test_validate_config_from_env(self, monkeypatch):
        """Test validate_config reads from os.environ."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "env-token")
        monkeypatch.setenv("GROQ_API_KEY", "env-key")
        # Should not raise
        validate_config()
