"""Tests for product search functionality."""

import pytest
from handlers.product_search import _search_products


class TestProductSearch:
    def test_search_by_name(self):
        """Test searching products by name."""
        results = _search_products("earbuds")
        assert len(results) > 0
        assert any("Earbuds" in p["name"] for p in results)
    
    def test_search_case_insensitive(self):
        """Test search is case-insensitive."""
        results_lower = _search_products("webcam")
        results_upper = _search_products("WEBCAM")
        assert len(results_lower) == len(results_upper)
    
    def test_search_by_category(self):
        """Test searching by category."""
        results = _search_products("audio")
        assert len(results) > 0
        assert all(r["category"] == "Audio" for r in results)
    
    def test_search_partial_match(self):
        """Test partial word matching."""
        results = _search_products("phone")
        assert len(results) > 0
    
    def test_search_multiple_tokens(self):
        """Test searching with multiple keywords."""
        results = _search_products("usb hub")
        assert len(results) > 0
        assert any("Hub" in p["name"] for p in results)
    
    def test_search_limit(self):
        """Test search result limit."""
        results = _search_products("the", limit=3)
        assert len(results) <= 3
    
    def test_search_empty_query(self):
        """Test empty search returns empty."""
        results = _search_products("")
        assert len(results) == 0
    
    def test_search_no_results(self):
        """Test nonexistent product returns empty."""
        results = _search_products("xyz_nonexistent_product_123")
        assert len(results) == 0
    
    def test_in_stock_ranking(self):
        """Test that in-stock products rank higher."""
        # This is a general property check
        results = _search_products("stand", limit=10)
        if len(results) > 1:
            # First result should preferably be in stock
            assert results[0]["in_stock"] or not any(p["in_stock"] for p in results)
