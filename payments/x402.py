import hashlib
import hmac
import json
import logging
import os
import threading
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

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "x402_data.json")
_lock = threading.Lock()

_balances: dict[str, float] = {}
_transactions: list[dict] = []
_loaded = False


def _load():
    global _loaded, _balances, _transactions
    if _loaded:
        return
    _loaded = True
    try:
        path = os.path.abspath(DATA_FILE)
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
                _balances = data.get("balances", {})
                _transactions = data.get("transactions", [])
            logger.info("Loaded x402 data: %d users, %d txns", len(_balances), len(_transactions))
    except Exception as e:
        logger.warning("Failed to load x402 data: %s", e)


def _save():
    try:
        path = os.path.abspath(DATA_FILE)
        with open(path, "w") as f:
            json.dump({"balances": _balances, "transactions": _transactions}, f, indent=2)
    except Exception as e:
        logger.error("Failed to save x402 data: %s", e)


def get_tool_price(tool_name: str) -> float:
    return PRICING.get(tool_name, 0.01)


def get_balance(user_id: str) -> float:
    _load()
    with _lock:
        if user_id not in _balances:
            _balances[user_id] = INITIAL_CREDITS
            _save()
        return round(_balances[user_id], 4)


def ensure_user(user_id: str):
    _load()
    with _lock:
        if user_id not in _balances:
            _balances[user_id] = INITIAL_CREDITS
            _save()


def deduct_balance(user_id: str, amount: float, tool: str = "") -> bool:
    _load()
    with _lock:
        if user_id not in _balances:
            _balances[user_id] = INITIAL_CREDITS
        bal = _balances[user_id]
        if bal < amount:
            _save()
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
        _save()
    return True


def add_credits(user_id: str, amount: float, note: str = ""):
    _load()
    with _lock:
        bal = _balances.get(user_id, INITIAL_CREDITS)
        _balances[user_id] = round(bal + amount, 4)
        _transactions.append({
            "type": "credit",
            "user_id": user_id,
            "amount": amount,
            "note": note,
            "balance_after": _balances[user_id],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        _save()


def get_transactions(user_id: Optional[str] = None, limit: int = 50) -> list[dict]:
    _load()
    txns = _transactions
    if user_id:
        txns = [t for t in txns if t["user_id"] == user_id]
    return list(reversed(txns))[:limit]


def get_all_balances() -> dict[str, float]:
    _load()
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
    return {
        "balance": get_balance(user_id),
        "pricing": PRICING,
        "initial_credits": INITIAL_CREDITS,
    }
