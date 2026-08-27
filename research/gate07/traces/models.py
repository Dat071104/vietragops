"""Method-facing verified trace shape for Gate 07."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PublicVerifiedTrace:
    trace_id: str
    tool_name: str
    version: str
    normalized_input: dict[str, Any]
    output: dict[str, Any]
    state_hash_before: str
    state_hash_after: str
    sequence: int
    verified: bool
