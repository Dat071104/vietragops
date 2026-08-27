"""Minimal, bounded, deterministic audit trail for MCP tool calls.

Records only: timestamp, request id, tool name, authorized outcome, status.
Never records the bearer token, raw tool arguments, or retrieved source
content. Bounded by a fixed-size ring buffer so it cannot grow without
bound in a long-running process.
"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import threading

DEFAULT_AUDIT_LOG_MAXLEN = 500


@dataclass(frozen=True)
class AuditRecord:
    timestamp: str
    request_id: str
    tool_name: str
    authorized: bool
    status: str  # "ok" | "denied" | "error"


class McpAuditLog:
    def __init__(self, maxlen: int = DEFAULT_AUDIT_LOG_MAXLEN) -> None:
        self._records: deque[AuditRecord] = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def record(self, *, request_id: str, tool_name: str, authorized: bool, status: str) -> AuditRecord:
        entry = AuditRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            request_id=request_id,
            tool_name=tool_name,
            authorized=authorized,
            status=status,
        )
        with self._lock:
            self._records.append(entry)
        return entry

    def snapshot(self) -> list[dict]:
        with self._lock:
            return [asdict(entry) for entry in self._records]

    def __len__(self) -> int:
        with self._lock:
            return len(self._records)
