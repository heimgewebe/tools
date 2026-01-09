
import pytest
import datetime
import contextlib
from merger.lenskit.core import clock

def test_clock_now_utc_is_aware_and_utc():
    """Ensure now_utc() returns timezone-aware UTC datetime."""
    now = clock.now_utc()
    assert now.tzinfo == datetime.timezone.utc
    # Sanity check it's close to system time (if not frozen)
    system_now = datetime.datetime.now(datetime.timezone.utc)
    assert abs((system_now - now).total_seconds()) < 1.0

def test_clock_frozen_context_restores_previous_state():
    """Ensure nested frozen contexts restore previous state correctly."""
    t1 = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    t2 = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)

    # Initial state: real time
    real_time = clock.now_utc()

    with clock.frozen(t1):
        assert clock.now_utc() == t1

        with clock.frozen(t2):
            assert clock.now_utc() == t2

        # Should restore to t1
        assert clock.now_utc() == t1

    # Should restore to real time (approximately)
    now_after = clock.now_utc()
    assert abs((now_after - real_time).total_seconds()) < 0.1

def test_clock_freeze_time_none_resets_to_system_time():
    """Ensure freeze_time(None) unfreezes the clock."""
    t1 = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)

    clock.freeze_time(t1)
    assert clock.now_utc() == t1

    clock.freeze_time(None)
    # Should be back to system time
    now = clock.now_utc()
    assert now.tzinfo == datetime.timezone.utc
    assert now != t1
    # Check it is current
    system_now = datetime.datetime.now(datetime.timezone.utc)
    assert abs((system_now - now).total_seconds()) < 1.0

def test_clock_rejects_non_strict_utc():
    """Ensure non-UTC datetimes are rejected."""
    # Naive datetime
    naive = datetime.datetime(2023, 1, 1, 12, 0, 0)
    with pytest.raises(ValueError, match="must be strictly UTC"):
        clock.freeze_time(naive)

    with pytest.raises(ValueError, match="must be strictly UTC"):
        with clock.frozen(naive):
            pass

    # Non-UTC timezone (e.g. fixed offset that isn't strictly timezone.utc object check)
    offset = datetime.timezone(datetime.timedelta(hours=1))
    other_tz = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=offset)

    with pytest.raises(ValueError, match="must be strictly UTC"):
        clock.freeze_time(other_tz)
