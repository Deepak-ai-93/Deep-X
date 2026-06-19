import pytest
from middleware.rate_limit import check_rate_limit
from app.config import settings


class TestRateLimit:
    def test_first_request_passes(self):
        ok, retry = check_rate_limit("test-user-1")
        assert ok is True
        assert retry is None

    def test_multiple_requests_pass(self):
        uid = "test-user-2"
        for _ in range(5):
            ok, retry = check_rate_limit(uid)
            assert ok is True
