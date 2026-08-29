"""Shared prediction and raw-output records for baseline arms."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProposedMapping:
    case_id: str
    selected_tool_names: tuple[str, ...] = ()
    ranked_tool_names: tuple[str, ...] = ()
    argument_pairs: tuple[tuple[str, str, str, str], ...] = ()
    abstain: bool = False
    attempted_inputs: tuple[dict[str, Any], ...] = ()

    @classmethod
    def abstention(cls, case_id: str) -> "ProposedMapping":
        return cls(case_id=case_id, abstain=True)


@dataclass(frozen=True)
class RawOutputRecord:
    arm_id: str
    model: str
    case_id: str
    prompt_id: str | None
    rendered_prompt: str | None
    raw_response: str | None
    provider: str
    latency_ms: float
    token_usage: dict[str, Any] = field(default_factory=dict)
    outcome: str = "success"
    failure_kind: str | None = None
    error: str | None = None
    provider_error_body: str | None = None

    def to_record(self) -> dict[str, Any]:
        return {
            "arm_id": self.arm_id,
            "model": self.model,
            "case_id": self.case_id,
            "prompt_id": self.prompt_id,
            "rendered_prompt": self.rendered_prompt,
            "raw_response": self.raw_response,
            "provider": self.provider,
            "latency_ms": self.latency_ms,
            "token_usage": dict(self.token_usage),
            "outcome": self.outcome,
            "failure_kind": self.failure_kind,
            "error": self.error,
            "provider_error_body": self.provider_error_body,
        }
