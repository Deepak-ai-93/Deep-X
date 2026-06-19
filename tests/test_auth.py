import pytest
from middleware.auth import validate_api_key, register_api_key


class TestAuth:
    def test_register_and_validate(self):
        register_api_key("test-key-123", user_id=42)
        assert validate_api_key("test-key-123") == 42

    def test_invalid_key(self):
        assert validate_api_key("nonexistent-key") is None

    def test_register_multiple_keys(self):
        register_api_key("key-a", user_id=1)
        register_api_key("key-b", user_id=2)
        assert validate_api_key("key-a") == 1
        assert validate_api_key("key-b") == 2
