"""Read collected signatures back into method objects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from research.gate08.method.models import ArgumentSemantics, IntentSignature
from research.gate08.method.signature import attach_observed_values, literal_signature


def signature_from_record(record: dict[str, Any]) -> IntentSignature:
    return IntentSignature(
        side=record["side"],
        tool_name=record["tool_name"],
        operation=record["operation"],
        primary_entity=record["primary_entity"],
        target_entity=record.get("target_entity"),
        precondition_targets=tuple(record.get("precondition_targets", [])),
        effects=tuple((entry[0], entry[1]) for entry in record.get("effects", [])),
        arguments=tuple(
            ArgumentSemantics(
                name=argument["name"],
                concept=argument["concept"],
                value_shape=argument["value_shape"],
                required=argument.get("required", True),
                part_of=argument.get("part_of"),
                part_position=argument.get("part_position"),
                components=tuple(argument.get("components", [])),
                stated_literal=argument.get("stated_literal"),
                observed_value=argument.get("observed_value"),
                observed_delimiter=argument.get("observed_delimiter"),
            )
            for argument in record.get("arguments", [])
        ),
        output_semantics=tuple(record.get("output_semantics", [])),
    )


class SignatureStore:
    """Latest successful signature per collection key."""

    def __init__(self) -> None:
        self._old: dict[tuple[str, str, str, str], IntentSignature] = {}
        self._new: dict[tuple[str, str, str], IntentSignature] = {}
        self.outcomes: list[dict[str, Any]] = []

    @classmethod
    def load(cls, path: str | Path) -> "SignatureStore":
        store = cls()
        target = Path(path)
        if not target.exists():
            return store
        for line in target.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            store.outcomes.append(
                {
                    "kind": row.get("kind"),
                    "variant": row.get("variant"),
                    "model": row.get("model"),
                    "case_id": row.get("case_id"),
                    "tool_name": row.get("tool_name"),
                    "outcome": row.get("outcome"),
                    "failure_kind": row.get("failure_kind"),
                }
            )
            if row.get("outcome") != "success" or not row.get("signature"):
                continue
            signature = signature_from_record(row["signature"])
            if row["kind"] == "old":
                store._old[(row["model"], row["variant"], row["case_id"], row["tool_name"])] = signature
            else:
                store._new[(row["model"], row["tool_name"], row["schema_hash"])] = signature
        return store

    def old_signature(
        self,
        *,
        model: str,
        variant: str,
        task: dict[str, Any],
        with_traces: bool,
    ) -> IntentSignature | None:
        tool_names = task.get("old_tool_names", [])
        if not tool_names:
            return None
        signature = self._old.get((model, variant, task["case_id"], tool_names[0]))
        if signature is None:
            return None
        if not with_traces:
            return signature
        return attach_observed_values(signature, task.get("verified_old_traces", []))

    def candidate_signatures(self, *, model: str, task: dict[str, Any]) -> dict[str, IntentSignature]:
        found: dict[str, IntentSignature] = {}
        for contract in task.get("new_contracts", []):
            signature = self._new.get((model, contract["name"], contract["schema_hash"]))
            if signature is not None:
                found[contract["name"]] = signature
        return found


def literal_old_signature(task: dict[str, Any], *, with_traces: bool) -> IntentSignature | None:
    """The `no intent abstraction` old side: the contract, unabstracted."""
    tool_names = task.get("old_tool_names", [])
    contracts = {contract["name"]: contract for contract in task.get("old_contracts", [])}
    if not tool_names or tool_names[0] not in contracts:
        return None
    signature = literal_signature(contracts[tool_names[0]], side="old")
    if not with_traces:
        return signature
    return attach_observed_values(signature, task.get("verified_old_traces", []))


def literal_candidate_signatures(task: dict[str, Any]) -> dict[str, IntentSignature]:
    return {
        contract["name"]: literal_signature(contract, side="new")
        for contract in task.get("new_contracts", [])
    }


__all__ = [
    "SignatureStore",
    "literal_candidate_signatures",
    "literal_old_signature",
    "signature_from_record",
]
