from __future__ import annotations

from datetime import datetime, timezone

import pytest

from rag.generation.openrouter_client import DailyRequestLedger, OpenRouterRateLimitError, RequestRateGovernor


class FakeClock:
    def __init__(self, value: datetime):
        self.value = value

    def __call__(self) -> datetime:
        return self.value


def test_reserve_and_settle_consumed_request():
    ledger = DailyRequestLedger(2)

    reservation = ledger.reserve()
    assert ledger.snapshot()["remaining"] == 1
    ledger.settle(reservation, consumed=True)

    snapshot = ledger.snapshot()
    assert snapshot["used"] == 1
    assert snapshot["reserved"] == 0
    assert snapshot["remaining"] == 1


def test_not_sent_settlement_releases_reservation():
    ledger = DailyRequestLedger(1)
    reservation = ledger.reserve()
    ledger.settle(reservation, consumed=False)

    assert ledger.snapshot()["used"] == 0
    assert ledger.snapshot()["remaining"] == 1


def test_ambiguous_outcome_retains_reservation_as_consumed():
    ledger = DailyRequestLedger(1)
    reservation = ledger.reserve()
    ledger.settle(reservation, consumed=True)

    with pytest.raises(OpenRouterRateLimitError):
        ledger.reserve()


def test_ceiling_refuses_next_request_before_transport():
    ledger = DailyRequestLedger(1)
    ledger.settle(ledger.reserve(), consumed=True)

    with pytest.raises(OpenRouterRateLimitError) as exc_info:
        ledger.reserve()

    assert exc_info.value.status_code == 429
    assert exc_info.value.local_budget is True


def test_utc_day_rollover_resets_allowance():
    clock = FakeClock(datetime(2026, 9, 8, 23, 59, tzinfo=timezone.utc))
    ledger = DailyRequestLedger(1, clock=clock)
    ledger.settle(ledger.reserve(), consumed=True)
    assert ledger.snapshot()["remaining"] == 0

    clock.value = datetime(2026, 9, 9, 0, 0, tzinfo=timezone.utc)
    assert ledger.snapshot()["remaining"] == 1
    ledger.settle(ledger.reserve(), consumed=True)
    assert ledger.snapshot()["used"] == 1


def test_rate_governor_counts_every_dispatch_and_enforces_under_20_rpm():
    now = [0.0]
    sleeps = []

    def clock():
        return now[0]

    def sleep(seconds):
        sleeps.append(seconds)
        now[0] += seconds

    governor = RequestRateGovernor(clock=clock, sleep_fn=sleep)
    governor.acquire()
    governor.acquire()
    governor.acquire()

    snapshot = governor.snapshot()
    assert snapshot["dispatched"] == 3
    assert snapshot["min_interval_seconds"] == 3.1
    assert sleeps == [3.1, 3.1]
