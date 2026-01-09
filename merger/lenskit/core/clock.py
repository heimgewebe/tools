"""
Central time source for lenskit.
Provides deterministic time for testing and consistent UTC timestamps.
"""
import datetime
from typing import Optional

_frozen_time: Optional[datetime.datetime] = None

def now_utc() -> datetime.datetime:
    """
    Returns the current time in UTC.
    If time is frozen (via `freeze_time`), returns the frozen time.
    """
    if _frozen_time:
        return _frozen_time
    return datetime.datetime.now(datetime.timezone.utc)

def freeze_time(dt: Optional[datetime.datetime]) -> None:
    """
    Freeze the time to a specific datetime.
    Pass None to unfreeze.
    """
    global _frozen_time
    if dt is not None and dt.tzinfo is None:
        raise ValueError("Frozen time must be timezone-aware (UTC)")
    _frozen_time = dt
