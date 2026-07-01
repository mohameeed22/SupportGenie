# Testing Guide for SupportGenie

## Running Tests

### Quick Start
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_session_store.py

# Run specific test class
pytest tests/test_session_store.py::TestUserProfile

# Run specific test
pytest tests/test_session_store.py::TestUserProfile::test_upsert_and_get_user
```

### Coverage Report
```bash
pip install pytest-cov
pytest --cov=. --cov-report=html tests/
```

## Test Modules

### `test_session_store.py`
Database persistence layer tests:
- **TestUserProfile** — User creation, updates, and retrieval
- **TestConversationHistory** — Message recording, history limits, clearing
- **TestAnalytics** — Event logging, escalations, feedback
- **TestRateLimiting** — Rate limit enforcement per user

### `test_sentiment.py`
Sentiment analysis tests:
- **TestSentimentScoring** — Positive, negative, neutral message detection
- **TestEscalationTriggers** — Escalation on keywords ("human", "manager", etc.) and anger scores

### `test_product_search.py`
Product search ranking tests:
- Search by name, category, partial match
- Case-insensitive search
- Multiple keyword queries
- In-stock preference ranking

### `test_store_context.py`
Language detection and system prompt building:
- **TestLanguageDetection** — 10+ language detection (English, Spanish, Russian, Arabic, CJK, etc.)
- **TestSystemPromptBuilding** — Dynamic prompt injection with user context

### `test_config.py`
Configuration validation with Pydantic:
- Required fields enforcement
- Default value application
- Admin ID parsing (CSV, list, empty)
- Rate limit constraints
- Environment variable validation

### `test_order_tracking.py`
Order ID normalization and lookup:
- Order ID format normalization
- Order database lookup
- Invalid format handling

## Fixtures (conftest.py)

### `mock_env`
Auto-applied fixture that sets required environment variables for all tests:
- `TELEGRAM_BOT_TOKEN`, `GROQ_API_KEY`, `GROQ_MODEL`
- `SUPPORTGENIE_DB_PATH` (in-memory for tests)

### `test_user_id`
Standard test user ID: `123456789`

### `test_user_data`
Sample user profile dictionary with username, full_name, etc.

### `temp_db`
Creates temporary SQLite database for file-based tests (optional).

## CI/CD Integration

### Docker Testing
```bash
# Build and test in Docker
docker build -t supportgenie-test .
docker run supportgenie-test pytest

# With coverage
docker run supportgenie-test pytest --cov=. tests/
```

### GitHub Actions (example)
```yaml
- name: Run tests
  run: pytest -v --tb=short
  
- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Test Coverage Goals

| Module | Coverage | Status |
| --- | --- | --- |
| `db/session_store.py` | 85%+ | ✓ Comprehensive |
| `handlers/sentiment.py` | 90%+ | ✓ Keyword coverage |
| `handlers/product_search.py` | 80%+ | ✓ Ranking logic |
| `store_context.py` | 95%+ | ✓ Language detection |
| `config.py` | 100% | ✓ Pydantic validation |

## Common Issues

### ImportError: No module named 'pytest'
```bash
pip install -r requirements.txt
```

### Database locked error
The conftest.py uses in-memory SQLite (`:memory:`) by default, avoiding file locks.

### Async test failures
Make sure `pytest-asyncio` is installed:
```bash
pip install pytest-asyncio
```

## Writing New Tests

1. Create test file in `tests/` directory: `test_new_module.py`
2. Use fixture-based setup from `conftest.py`
3. Name test functions `test_*` (pytest convention)
4. Run: `pytest tests/test_new_module.py -v`

Example:
```python
def test_my_feature(test_user_id):
    """Test a specific feature."""
    from my_module import my_function
    result = my_function(test_user_id)
    assert result is not None
```
