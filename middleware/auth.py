import hashlib
import logging
from typing import Optional
from fastapi import Request, HTTPException
from app.config import settings

logger = logging.getLogger(__name__)

_valid_keys: dict[str, int] = {}


def validate_api_key(key: str) -> Optional[int]:
    if key in _valid_keys:
        return _valid_keys[key]
    return None


def register_api_key(key: str, user_id: int):
    _valid_keys[key] = user_id


async def authenticate_request(request: Request) -> int:
    key = request.headers.get(settings.api_key_header)
    if not key:
        raise HTTPException(status_code=401, detail="Missing API key")
    user_id = validate_api_key(key)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user_id
