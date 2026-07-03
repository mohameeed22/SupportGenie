"""Tests for order tracking utilities."""

from types import SimpleNamespace

from handlers import order_tracking
from handlers.order_tracking import normalize_order_id, lookup_order


class TestOrderIdNormalization:
    def test_normalize_with_prefix(self):
        """Test normalizing order ID with NB- prefix."""
        assert normalize_order_id("NB-12345") == "NB-12345"

    def test_normalize_without_prefix(self):
        """Test normalizing order ID without prefix adds it."""
        assert normalize_order_id("12345") == "NB-12345"

    def test_normalize_removes_spaces(self):
        """Test normalization removes spaces."""
        assert normalize_order_id("NB- 12345") == "NB-12345"
        assert normalize_order_id(" 12345 ") == "NB-12345"

    def test_normalize_uppercase(self):
        """Test normalization uppercases prefix."""
        assert normalize_order_id("nb-12345") == "NB-12345"

    def test_normalize_idempotent(self):
        """Test normalizing twice gives same result."""
        once = normalize_order_id("12345")
        twice = normalize_order_id(once)
        assert once == twice


class TestOrderLookup:
    def test_lookup_valid_order(self):
        """Test looking up a valid order."""
        order = lookup_order("NB-00001")
        assert order is not None
        assert order["id"] == "NB-00001"

    def test_lookup_order_without_prefix(self):
        """Test looking up order without prefix."""
        order = lookup_order("00001")
        assert order is not None
        assert order["id"] == "NB-00001"

    def test_lookup_nonexistent_order(self):
        """Test looking up nonexistent order returns None."""
        order = lookup_order("NB-99999")
        assert order is None

    def test_lookup_invalid_format(self):
        """Test invalid order format returns None."""
        order = lookup_order("invalid")
        assert order is None

    def test_order_contains_required_fields(self):
        """Test returned order has required fields."""
        order = lookup_order("NB-00001")
        if order:
            assert "id" in order
            assert "user_id" in order
            assert "total" in order
            assert "status" in order

    def test_lookup_uses_live_api_when_available(self, monkeypatch):
        monkeypatch.setattr(order_tracking.config, "ORDER_LOOKUP_URL", "https://api.example.com/orders")
        monkeypatch.setattr(order_tracking.config, "ORDER_LOOKUP_API_KEY", "secret")
        monkeypatch.setattr(order_tracking.config, "ORDER_LOOKUP_TIMEOUT_SECONDS", 2)

        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {"order": {"order_id": "NB-55555", "status": "Shipped", "item": "Test"}}

        captured = {}

        def fake_get(url, headers=None, timeout=None):
            captured["url"] = url
            captured["headers"] = headers
            captured["timeout"] = timeout
            return FakeResponse()

        monkeypatch.setattr(order_tracking.httpx, "get", fake_get)

        order = lookup_order("NB-55555")

        assert order is not None
        assert order["order_id"] == "NB-55555"
        assert order["status"] == "Shipped"
        assert captured["url"].endswith("/NB-55555")
        assert captured["headers"]["Authorization"] == "Bearer secret"
        assert captured["timeout"] == 2
