"""Tests for store context and language detection."""

import pytest
from store_context import detect_language, build_system_prompt


class TestLanguageDetection:
    def test_detect_english(self):
        """Test English detection."""
        assert detect_language("What is your shipping policy?") == "English"
    
    def test_detect_spanish(self):
        """Test Spanish detection."""
        assert detect_language("Hola, ¿cuál es tu precio?") == "Spanish"
    
    def test_detect_french(self):
        """Test French detection."""
        assert detect_language("Bonjour, comment allez-vous?") == "French"
    
    def test_detect_german(self):
        """Test German detection."""
        assert detect_language("Hallo, wie geht es dir?") == "German"
    
    def test_detect_portuguese(self):
        """Test Portuguese detection."""
        assert detect_language("Olá, como você está?") == "Portuguese"
    
    def test_detect_russian_cyrillic(self):
        """Test Russian (Cyrillic) detection."""
        assert detect_language("Привет, как дела?") == "Russian"
    
    def test_detect_arabic(self):
        """Test Arabic detection."""
        assert detect_language("مرحبا، كيف حالك؟") == "Arabic"
    
    def test_detect_chinese(self):
        """Test Chinese detection."""
        assert detect_language("你好，你好吗？") == "Chinese"
    
    def test_detect_japanese(self):
        """Test Japanese detection."""
        assert detect_language("こんにちは、元気ですか？") == "Japanese"
    
    def test_detect_hindi(self):
        """Test Hindi detection."""
        assert detect_language("नमस्ते, आप कैसे हैं?") == "Hindi"
    
    def test_default_to_english(self):
        """Test fallback to English for unrecognized."""
        assert detect_language("12345 !@#$%") == "English"
    
    def test_case_insensitive_keywords(self):
        """Test keyword detection is case-insensitive."""
        assert detect_language("GRACIAS, HOLA") == "Spanish"
        assert detect_language("Merci, Bonjour") == "French"


class TestSystemPromptBuilding:
    def test_base_prompt_contains_requirements(self):
        """Test system prompt includes key requirements."""
        prompt = build_system_prompt()
        assert "Genie" in prompt
        assert "NovaBuy" in prompt
        assert "customer support" in prompt
    
    def test_language_preference_injected(self):
        """Test language preference is included in prompt."""
        prompt = build_system_prompt(preferred_language="Spanish")
        assert "Spanish" in prompt
    
    def test_user_name_injected(self):
        """Test user name is included when provided."""
        prompt = build_system_prompt(user_name="Alice")
        assert "Alice" in prompt
    
    def test_extra_context_injected(self):
        """Test extra context is appended."""
        extra = "Special context for this query"
        prompt = build_system_prompt(extra_context=extra)
        assert extra in prompt
        assert "EXTRA CONTEXT" in prompt
    
    def test_all_parameters_combined(self):
        """Test all parameters together."""
        prompt = build_system_prompt(
            preferred_language="German",
            user_name="Bob",
            extra_context="Return request context"
        )
        assert "German" in prompt
        assert "Bob" in prompt
        assert "Return request context" in prompt
    
    def test_no_extra_context_no_section(self):
        """Test EXTRA CONTEXT section not present when empty."""
        prompt_without = build_system_prompt(extra_context=None)
        assert "EXTRA CONTEXT:" not in prompt_without
    
    def test_product_list_included(self):
        """Test product list is included in system prompt."""
        prompt = build_system_prompt()
        assert "SoundWave Pro Earbuds" in prompt or "PRODUCT CATALOG" in prompt
    
    def test_policies_included(self):
        """Test policies are included in system prompt."""
        prompt = build_system_prompt()
        assert "RETURN POLICY" in prompt or "SHIPPING POLICY" in prompt
