"""Single-process request and token budget ledger for Gate 07 LLM runs."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
import time
from typing import Any


_WINDOW_EPSILON_SECONDS = 0.001


@dataclass(frozen=True)
class RateLimits:
    per_key: dict[str, int]
    pool: dict[str, int]
    org: dict[str, int]
    reserve_fraction: float = 0.20


class RateLimitLedger:
    """Enforce configured pool/org soft ceilings without adding key rotation."""

    def __init__(self, database: str | Path, request_log: str | Path, limits: RateLimits) -> None:
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self.request_log = Path(request_log)
        self.request_log.parent.mkdir(parents=True, exist_ok=True)
        self.limits = limits
        self.connection = sqlite3.connect(self.database)
        self.connection.execute("CREATE TABLE IF NOT EXISTS attempts (at REAL NOT NULL, input_tokens INTEGER NOT NULL, output_tokens INTEGER NOT NULL, arm_id TEXT NOT NULL, model TEXT NOT NULL, case_id TEXT NOT NULL, outcome TEXT NOT NULL)")
        self.connection.commit()

    def _usage(self, since: float) -> tuple[int, int, int]:
        row = self.connection.execute("SELECT COUNT(*), COALESCE(SUM(input_tokens), 0), COALESCE(SUM(output_tokens), 0) FROM attempts WHERE at >= ?", (since,)).fetchone()
        return int(row[0]), int(row[1]), int(row[2])

    def _rows_since(self, since: float) -> list[tuple[float, int, int]]:
        rows = self.connection.execute(
            "SELECT at, input_tokens, output_tokens FROM attempts WHERE at >= ? ORDER BY at ASC",
            (since,),
        ).fetchall()
        return [(float(at), int(input_tokens), int(output_tokens)) for at, input_tokens, output_tokens in rows]

    def _cap(self, value: int) -> int:
        return max(1, int(value * (1 - self.limits.reserve_fraction)))

    def allow(self, input_tokens: int, output_tokens: int) -> tuple[bool, str | None]:
        now = time.time()
        minute_count, minute_input, minute_output = self._usage(now - 60)
        day_count, day_input, day_output = self._usage(now - 86400)
        checks = (
            (minute_count + 1, self._cap(self.limits.pool["rpm"]), "pool_rpm"),
            (minute_input + input_tokens, self._cap(self.limits.pool["tpm"]), "pool_tpm"),
            (day_count + 1, self._cap(self.limits.pool["rpd"]), "pool_rpd"),
            (day_input + input_tokens + output_tokens, self._cap(self.limits.pool["tpd"]), "pool_tpd"),
            (minute_count + 1, self._cap(self.limits.org["rpm"]), "org_rpm"),
            (minute_input + input_tokens, self._cap(self.limits.org["tpm"]), "org_tpm"),
            (day_count + 1, self._cap(self.limits.org["rpd"]), "org_rpd"),
            (day_input + input_tokens + output_tokens, self._cap(self.limits.org["tpd"]), "org_tpd"),
        )
        for used, cap, label in checks:
            if used > cap:
                return False, label
        return True, None

    @staticmethod
    def _count_wait(rows: list[tuple[float, int, int]], cap: int, window_seconds: float, now: float) -> float:
        expired_needed = len(rows) + 1 - cap
        if expired_needed <= 0:
            return 0.0
        if expired_needed > len(rows):
            return 0.0
        return max(0.0, rows[expired_needed - 1][0] + window_seconds - now + _WINDOW_EPSILON_SECONDS)

    @staticmethod
    def _token_wait(
        rows: list[tuple[float, int, int]],
        request_tokens: int,
        cap: int,
        token_kind: str,
        window_seconds: float,
        now: float,
    ) -> float:
        # A request larger than the configured cap can never become admissible
        # by expiry alone. Return immediately so the caller can exhaust its
        # bounded retry policy and classify the row as client_throttled.
        if request_tokens > cap:
            return 0.0
        used = sum(row[1] if token_kind == "input" else row[1] + row[2] for row in rows)
        excess = used + request_tokens - cap
        if excess <= 0:
            return 0.0
        released = 0
        for row in rows:
            released += row[1] if token_kind == "input" else row[1] + row[2]
            if released >= excess:
                return max(0.0, row[0] + window_seconds - now + _WINDOW_EPSILON_SECONDS)
        return 0.0

    def wait_time(self, input_tokens: int, output_tokens: int) -> float:
        """Return seconds until the currently blocking soft cap can release.

        This is a read-only calculation. It deliberately does not insert a
        reservation or an attempt: a request that has not been sent must not
        consume the ledger budget. If the request itself exceeds a token cap,
        the corresponding wait is zero because expiry cannot make it fit; the
        caller's bounded retry policy then records a typed client throttle.
        """
        now = time.time()
        minute_rows = self._rows_since(now - 60)
        day_rows = self._rows_since(now - 86400)
        waits = [
            self._count_wait(minute_rows, self._cap(self.limits.pool["rpm"]), 60, now),
            self._token_wait(minute_rows, input_tokens, self._cap(self.limits.pool["tpm"]), "input", 60, now),
            self._count_wait(day_rows, self._cap(self.limits.pool["rpd"]), 86400, now),
            self._token_wait(day_rows, input_tokens + output_tokens, self._cap(self.limits.pool["tpd"]), "total", 86400, now),
            self._count_wait(minute_rows, self._cap(self.limits.org["rpm"]), 60, now),
            self._token_wait(minute_rows, input_tokens, self._cap(self.limits.org["tpm"]), "input", 60, now),
            self._count_wait(day_rows, self._cap(self.limits.org["rpd"]), 86400, now),
            self._token_wait(day_rows, input_tokens + output_tokens, self._cap(self.limits.org["tpd"]), "total", 86400, now),
        ]
        return max(waits, default=0.0)

    def record(self, *, arm_id: str, model: str, case_id: str, input_tokens: int, output_tokens: int, outcome: str) -> None:
        now = time.time()
        self.connection.execute("INSERT INTO attempts(at, input_tokens, output_tokens, arm_id, model, case_id, outcome) VALUES (?, ?, ?, ?, ?, ?, ?)", (now, input_tokens, output_tokens, arm_id, model, case_id, outcome))
        self.connection.commit()
        with self.request_log.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps({"at": now, "arm_id": arm_id, "model": model, "case_id": case_id, "input_tokens": input_tokens, "output_tokens": output_tokens, "outcome": outcome}, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n")

    def close(self) -> None:
        self.connection.close()


def limits_from_environment() -> RateLimits:
    import os

    per_key = {"rpm": int(os.environ["GROQ_RPM_SOFT_PER_KEY"]), "tpm": int(os.environ["GROQ_TPM_SOFT_PER_KEY"]), "rpd": int(os.environ["GROQ_RPD_SOFT_PER_KEY"]), "tpd": int(os.environ["GROQ_TPD_SOFT_PER_KEY"])}
    pool = {"rpm": int(os.environ["GROQ_POOL_RPM_SOFT"]), "tpm": int(os.environ["GROQ_POOL_TPM_SOFT"]), "rpd": int(os.environ["GROQ_POOL_RPD_SOFT"]), "tpd": int(os.environ["GROQ_POOL_TPD_SOFT"])}
    org = {"rpm": int(os.environ["GROQ_ORG_RPM_SOFT"]), "tpm": int(os.environ["GROQ_ORG_TPM_SOFT"]), "rpd": int(os.environ["GROQ_ORG_RPD_SOFT"]), "tpd": int(os.environ["GROQ_ORG_TPD_SOFT"])}
    return RateLimits(per_key=per_key, pool=pool, org=org)
