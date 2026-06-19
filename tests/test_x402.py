import pytest
from payments.x402 import get_tool_price, create_x402_token, verify_x402_token
from app.config import settings


class TestPricing:
    def test_known_tool_price(self):
        assert get_tool_price("generate_linkedin_post") == 0.01
        assert get_tool_price("generate_x_content") == 0.01
        assert get_tool_price("analyze_content") == 0.005
        assert get_tool_price("generate_content_pack") == 0.03

    def test_unknown_tool_default(self):
        assert get_tool_price("unknown_tool") == 0.01

    def test_all_prices_positive(self):
        from payments.x402 import PRICING
        for name, price in PRICING.items():
            assert price > 0, f"{name} has non-positive price"


class TestX402Token:
    def test_create_and_verify(self):
        settings.x402_secret = "test-secret"
        token = create_x402_token(0.01)
        assert token is not None
        assert verify_x402_token(token or "", 0.01)

    def test_wrong_amount_fails(self):
        settings.x402_secret = "test-secret"
        token = create_x402_token(0.01)
        assert not verify_x402_token(token, 0.02)

    def test_bad_token_fails(self):
        settings.x402_secret = "test-secret"
        assert not verify_x402_token("invalid:token", 0.01)

    def test_disabled_when_no_secret(self):
        settings.x402_secret = None
        assert create_x402_token(0.01) is None
        assert verify_x402_token("anything", 0.01)
