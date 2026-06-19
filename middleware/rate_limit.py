import time
import logging
from collections import defaultdict
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

_window: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(key: str) -> tuple[bool, Optional[int]]:
    now = time.time()
    window_start = now - settings.rate_limit_window
    timestamps = [t for t in _window[key] if t > window_start]
    _window[key] = timestamps
    if len(timestamps) >= settings.rate_limit_requests:
        retry_after = int(timestamps[0] + settings.rate_limit_window - now)
        return False, max(retry_after, 1)
    _window[key].append(now)
    return True, None
