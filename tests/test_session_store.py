"""Tests for database session_store module."""

from db import session_store


class TestUserProfile:
    def test_upsert_and_get_user(self, test_user_id, test_user_data):
        """Test creating and retrieving a user profile."""
        session_store.upsert_user(test_user_id, **test_user_data)

        profile = session_store.get_user_profile(test_user_id)
        assert profile is not None
        assert profile["user_id"] == test_user_id
        assert profile["username"] == test_user_data["username"]
        assert profile["full_name"] == test_user_data["full_name"]

    def test_upsert_updates_existing(self, test_user_id):
        """Test that upsert updates existing user."""
        session_store.upsert_user(test_user_id, full_name="Old Name")
        session_store.upsert_user(test_user_id, full_name="New Name")

        profile = session_store.get_user_profile(test_user_id)
        assert profile["full_name"] == "New Name"

    def test_nonexistent_user_returns_none(self):
        """Test that nonexistent user returns None."""
        profile = session_store.get_user_profile(999999)
        assert profile is None


class TestConversationHistory:
    def test_record_and_retrieve_messages(self, test_user_id):
        """Test recording and retrieving conversation history."""
        session_store.upsert_user(test_user_id)
        session_store.record_user_message(test_user_id, "Hello bot")
        session_store.record_assistant_message(test_user_id, "Hello human")

        messages = session_store.get_recent_messages(test_user_id, limit=10)
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello bot"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Hello human"

    def test_message_limit(self, test_user_id):
        """Test that message history respects limit."""
        session_store.upsert_user(test_user_id)

        for i in range(30):
            session_store.record_user_message(test_user_id, f"Message {i}")

        messages = session_store.get_recent_messages(test_user_id, limit=10)
        assert len(messages) == 10
        assert "Message 29" in messages[-1]["content"]

    def test_clear_conversation(self, test_user_id):
        """Test clearing conversation history."""
        session_store.upsert_user(test_user_id)
        session_store.record_user_message(test_user_id, "Test message")

        session_store.clear_conversation(test_user_id)
        messages = session_store.get_recent_messages(test_user_id)
        assert len(messages) == 0


class TestAnalytics:
    def test_record_event(self, test_user_id):
        """Test recording analytics events."""
        session_store.upsert_user(test_user_id)
        session_store.record_event(
            test_user_id,
            "question",
            question="What's your price?",
            answer="We offer competitive pricing",
        )

        # Should not raise exception
        assert session_store.count_events("question") >= 1

    def test_record_escalation(self, test_user_id):
        """Test recording escalations."""
        session_store.upsert_user(test_user_id)
        session_store.record_escalation(
            test_user_id, reason="sentiment-trigger", source="ai-chat"
        )

        # Should not raise exception
        assert session_store.count_events("escalation") >= 1

    def test_count_users(self, test_user_id):
        """Test counting total users."""
        session_store.upsert_user(test_user_id)
        session_store.upsert_user(test_user_id + 1)

        count = session_store.count_users()
        assert count >= 2

    def test_record_feedback(self, test_user_id):
        """Test recording feedback."""
        session_store.upsert_user(test_user_id)
        session_store.record_feedback(
            test_user_id, helpful=True, source="product-search"
        )

        # Should not raise exception
        assert session_store.count_events("feedback") >= 1


class TestSupportTickets:
    def test_create_and_read_ticket(self, test_user_id):
        session_store.upsert_user(test_user_id)
        ticket = session_store.create_support_ticket(
            test_user_id,
            "Need help with my order",
            source="telegram-escalation",
            reason="user-request",
            order_id="NB-10042",
            transcript=[{"role": "user", "content": "help"}],
            metadata={"channel": "telegram"},
        )

        assert ticket["ticket_id"] > 0
        assert ticket["status"] == "open"
        assert ticket["order_id"] == "NB-10042"
        assert ticket["transcript"][0]["content"] == "help"

    def test_list_and_resolve_ticket(self, test_user_id):
        session_store.upsert_user(test_user_id)
        ticket = session_store.create_support_ticket(
            test_user_id,
            "Refund issue",
            source="telegram-escalation",
        )

        open_tickets = session_store.list_support_tickets(status="open", limit=5)
        assert open_tickets
        assert open_tickets[0]["ticket_id"] == ticket["ticket_id"]

        resolved = session_store.update_support_ticket(
            ticket["ticket_id"],
            status="resolved",
            resolution_note="Handled by admin",
            assigned_to="agent-1",
        )
        assert resolved is not None
        assert resolved["status"] == "resolved"
        assert resolved["resolution_note"] == "Handled by admin"
        assert session_store.count_support_tickets(status="resolved") >= 1


class TestRateLimiting:
    def test_rate_limit_check_passes(self, test_user_id):
        """Test rate limiting allows messages within limit."""
        session_store.upsert_user(test_user_id)

        # First message should always pass
        limited = session_store.user_message_rate_limited(
            test_user_id, max_messages=5, window_seconds=60
        )
        assert not limited

    def test_rate_limit_blocks_excess_messages(self, test_user_id):
        """Test rate limiting blocks excess messages."""
        session_store.upsert_user(test_user_id)

        # Record several messages
        for _ in range(10):
            session_store.record_user_message(test_user_id, "Message")

        # Should hit rate limit with strict settings
        limited = session_store.user_message_rate_limited(
            test_user_id, max_messages=5, window_seconds=60
        )
        assert limited
