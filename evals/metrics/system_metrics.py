"""System-level latency and reliability metrics."""

from __future__ import annotations

import math
from typing import Any


def latency_summary(latencies_ms: list[float]) -> dict[str, float]:
    if not latencies_ms:
        return {"latency_p50_ms": 0.0, "latency_p95_ms": 0.0}
    ordered = sorted(latencies_ms)
    p50_index = int(math.floor((len(ordered) - 1) * 0.50))
    p95_index = int(math.floor((len(ordered) - 1) * 0.95))
    return {
        "latency_p50_ms": round(ordered[p50_index], 2),
        "latency_p95_ms": round(ordered[p95_index], 2),
    }


def error_rate(records: list[dict[str, Any]]) -> float:
    if not records:
        return 0.0
    errors = sum(1 for row in records if row.get("error"))
    return round(errors / len(records), 4)
