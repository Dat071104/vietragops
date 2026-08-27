from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class VerifiedTrace:
    """One real, executed sandbox call. Method-facing safe: `tool_id` here
    is the OLD tool's own identity, exposed alone; the correspondence
    secret this sandbox protects requires comparing it against a NEW
    tool's identity, which is never exposed anywhere method-facing (see
    `PublicToolContract`, which has no `tool_id` field at all).
    """

    trace_id: str
    tool_id: str
    tool_name: str
    version: str
    schema_hash: str
    normalized_input: dict[str, Any]
    precondition_outcome: str  # "satisfied" | "violated"
    output: dict[str, Any] | None
    state_hash_before: str
    state_hash_after: str
    sequence: int
    verified: bool
    error: str | None = None
