import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

PRICING: dict[str, float] = {
    "generate_linkedin_post": 0.01,
    "generate_x_content": 0.01,
    "analyze_content": 0.005,
    "improve_content": 0.005,
    "generate_content_pack": 0.03,
}

INITIAL_CREDITS: float = 0.0

_balances: dict[str, float] = {}
_transactions: list[dict] = []


def get_tool_price(tool_name: str) -> float:
    return PRICING.get(tool_name, 0.01)


def get_balance(user_id: str) -> float:
    if user_id not in _balances:
        _balances[user_id] = INITIAL_CREDITS
    return round(_balances[user_id], 4)


def deduct_balance(user_id: str, amount: float, tool: str = "") -> bool:
    bal = get_balance(user_id)
    if bal < amount:
        return False
    _balances[user_id] = round(bal - amount, 4)
    _transactions.append({
        "type": "debit",
        "user_id": user_id,
        "amount": amount,
        "tool": tool,
        "balance_after": _balances[user_id],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    return True


def add_credits(user_id: str, amount: float, note: str = ""):
    bal = get_balance(user_id)
    _balances[user_id] = round(bal + amount, 4)
    _transactions.append({
        "type": "credit",
        "user_id": user_id,
        "amount": amount,
        "note": note,
        "balance_after": _balances[user_id],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


def get_transactions(user_id: Optional[str] = None, limit: int = 50) -> list[dict]:
    txns = _transactions
    if user_id:
        txns = [t for t in txns if t["user_id"] == user_id]
    return list(reversed(txns))[:limit]


def get_all_balances() -> dict[str, float]:
    return dict(sorted(_balances.items(), key=lambda x: x[1], reverse=True))


def verify_x402_token(token: str, expected_amount: float) -> bool:
    if not settings.x402_secret:
        return True
    try:
        sep_idx = token.rfind(":")
        if sep_idx == -1:
            return False
        payload, sig = token[:sep_idx], token[sep_idx + 1:]
        expected_sig = hmac.new(
            settings.x402_secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()[:16]
        if not hmac.compare_digest(sig, expected_sig):
            return False
        data = json.loads(payload)
        return data.get("amount") == expected_amount
    except Exception:
        return False


def create_x402_token(amount: float) -> Optional[str]:
    if not settings.x402_secret:
        return None
    payload = json.dumps({"amount": amount, "version": 1})
    sig = hmac.new(
        settings.x402_secret.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()[:16]
    return f"{payload}:{sig}"


def get_pricing_with_balance(user_id: str) -> dict:
    bal = get_balance(user_id)
    return {
        "balance": bal,
        "pricing": PRICING,
        "initial_credits": INITIAL_CREDITS,
    }
