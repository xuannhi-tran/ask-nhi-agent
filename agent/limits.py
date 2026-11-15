"""In-memory rate limits so a public endpoint can't burn through the API credit.

Works because the service runs as a single replica (max-replicas 1).
"""

import os
import time
from collections import defaultdict

PER_IP_HOUR = int(os.getenv("LIMIT_PER_IP_HOUR", "10"))
PER_DAY = int(os.getenv("LIMIT_PER_DAY", "200"))

_hits: dict[str, list[float]] = defaultdict(list)


def allow(ip: str, now: float | None = None) -> str:
    """Returns 'ok', 'ip' (this visitor hit the hourly limit) or 'day' (site-wide daily cap)."""
    now = now or time.time()
    day = [t for t in _hits["__day__"] if now - t < 86400]
    mine = [t for t in _hits[ip] if now - t < 3600]
    _hits["__day__"], _hits[ip] = day, mine
    if len(day) >= PER_DAY:
        return "day"
    if len(mine) >= PER_IP_HOUR:
        return "ip"
    day.append(now)
    mine.append(now)
    return "ok"


def reset():
    _hits.clear()
