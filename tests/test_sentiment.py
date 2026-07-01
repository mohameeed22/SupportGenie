"""Tests for sentiment analysis module."""

import pytest
from handlers.sentiment import analyze_sentiment


class TestSentimentScoring:
    def test_positive_sentiment(self):
        """Test detection of positive messages."""
        result = analyze_sentiment("I love this product, great quality!")
        assert result.score > 0
        assert not result.escalate
    
    def test_negative_sentiment(self):
        """Test detection of negative messages."""
        result = analyze_sentiment("This is terrible and useless")
        assert result.score < 0
        assert not result.escalate  # Only escalates at threshold
    
    def test_neutral_sentiment(self):
        """Test neutral messages."""
        result = analyze_sentiment("What is your return policy?")
        assert result.score == 0
        assert not result.escalate


class TestEscalationTriggers:
    def test_escalate_on_high_anger(self):
        """Test escalation on very angry message."""
        result = analyze_sentiment("I am furious and absolutely hate this!")
        assert result.escalate
    
    def test_escalate_on_help_keyword(self):
        """Test escalation on 'human' keyword."""
        result = analyze_sentiment("I need to talk to a human agent")
        assert result.escalate
    
    def test_escalate_on_manager_keyword(self):
        """Test escalation on 'manager' keyword."""
        result = analyze_sentiment("I want to speak with a manager")
        assert result.escalate
    
    def test_escalate_on_agent_keyword(self):
        """Test escalation on 'agent' keyword."""
        result = analyze_sentiment("Can I talk to an agent?")
        assert result.escalate
    
    def test_escalate_on_supervisor_keyword(self):
        """Test escalation on 'supervisor' keyword."""
        result = analyze_sentiment("I need a supervisor")
        assert result.escalate
    
    def test_no_escalate_on_simple_question(self):
        """Test no escalation on simple question."""
        result = analyze_sentiment("What's the shipping cost?")
        assert not result.escalate
    
    def test_score_accumulation(self):
        """Test that anger words accumulate scores."""
        result = analyze_sentiment("I'm angry, frustrated, and furious")
        # Multiple negative words should produce lower score
        assert result.score < -2
