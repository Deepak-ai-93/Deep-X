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

DATA_FILE = os.path.abspath(os.path.join(os.getcwd(), "x402_data.json"))
_lock = threading.Lock()

_balances: dict[str, float] = {}
_transactions: list[dict] = []
_user_clients: dict[str, str] = {}
_loaded = False


def _load():
    global _loaded, _balances, _transactions, _user_clients
    if _loaded:
        return
    _loaded = True
    try:
        path = DATA_FILE
        logger.info("x402 data file path: %s", path)
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
                _balances = data.get("balances", {})
                _transactions = data.get("transactions", [])
                _user_clients = data.get("user_clients", {})
            logger.info(
                "Loaded x402 data: %d users, %d txns from %s",
                len(_balances), len(_transactions), path,
            )
        else:
            logger.info("No existing x402 data file at %s, starting fresh", path)
    except Exception as e:
        logger.warning("Failed to load x402 data: %s", e)


def _save():
    try:
        path = DATA_FILE
        with open(path, "w") as f:
            json.dump({
                "balances": _balances,
                "transactions": _transactions,
                "user_clients": _user_clients,
            }, f, indent=2)
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


def ensure_user(user_id: str, client: str = ""):
    _load()
    with _lock:
        if user_id not in _balances:
            _balances[user_id] = INITIAL_CREDITS
            _save()
        if client and _user_clients.get(user_id) != client:
            _user_clients[user_id] = client
            _save()


def deduct_balance(user_id: str, amount: float, tool: str = "") -> bool:
    _load()
    with _lock:
        if user_id not in _balances:
            _balances[user_id] = INITIAL_CREDITS
        bal = _balances[user_id]
        if bal < amount:
            _transactions.append({
                "type": "failed_debit",
                "user_id": user_id,
                "amount": amount,
                "tool": tool,
                "client": _user_clients.get(user_id, ""),
                "balance": bal,
                "reason": "insufficient_balance",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            _save()
            return False
        _balances[user_id] = round(bal - amount, 4)
        _transactions.append({
            "type": "debit",
            "user_id": user_id,
            "amount": amount,
            "tool": tool,
            "client": _user_clients.get(user_id, ""),
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


def get_all_users() -> list[dict]:
    _load()
    users = []
    for uid in _balances:
        users.append({
            "user_id": uid,
            "balance": _balances[uid],
            "client": _user_clients.get(uid, ""),
        })
    users.sort(key=lambda u: u["balance"], reverse=True)
    return users


def get_total_revenue() -> dict:
    _load()
    total_collected = 0.0
    paid_calls = 0
    total_credits_added = 0.0
    for txn in _transactions:
        if txn["type"] == "debit":
            total_collected += txn["amount"]
            paid_calls += 1
        elif txn["type"] == "credit":
            total_credits_added += txn["amount"]
    outstanding_balance = round(sum(_balances.values()), 4)
    return {
        "total_collected": round(total_collected, 4),
        "paid_calls": paid_calls,
        "total_credits_added": round(total_credits_added, 4),
        "outstanding_user_balances": outstanding_balance,
        "total_users": len(_balances),
    }


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
        "client": _user_clients.get(user_id, ""),
    }
