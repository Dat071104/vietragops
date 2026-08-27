"""Mechanically restricted baseline-arm interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from research.gate0.contracts import PublicToolContract

from research.gate07.harness.method_facing import MethodFacingTask
from research.gate07.traces.models import PublicVerifiedTrace
from research.gate07.baselines.models import ProposedMapping, RawOutputRecord


RIGHTS = frozenset({"old_contract", "new_contracts", "verified_old_traces", "task_description", "candidate_list"})


@dataclass(frozen=True)
class ArmInput:
    """Projection containing exactly the information rights granted to an arm."""

    case_id: str
    old_contracts: tuple[PublicToolContract, ...] = ()
    new_contracts: tuple[PublicToolContract, ...] = ()
    verified_old_traces: tuple[PublicVerifiedTrace, ...] = ()
    task_description: str | None = None
    candidate_new_tool_names: tuple[str, ...] = ()


def project_task(task: MethodFacingTask, information_rights: frozenset[str]) -> ArmInput:
    if not information_rights <= RIGHTS:
        raise ValueError(f"Unknown information right(s): {sorted(information_rights - RIGHTS)!r}")
    return ArmInput(
        case_id=task.case_id,
        old_contracts=task.old_contracts if "old_contract" in information_rights else (),
        new_contracts=task.new_contracts if "new_contracts" in information_rights else (),
        verified_old_traces=task.verified_old_traces if "verified_old_traces" in information_rights else (),
        task_description=task.task_description if "task_description" in information_rights else None,
        candidate_new_tool_names=task.candidate_new_tool_names if "candidate_list" in information_rights else (),
    )


class BaselineArm(ABC):
    """Every arm must declare rights and return an abstention-capable result."""

    arm_id: str
    information_rights: frozenset[str]

    def __init__(self, arm_id: str, information_rights: frozenset[str]) -> None:
        if not information_rights <= RIGHTS:
            raise ValueError("Baseline rights contain an unknown field.")
        self.arm_id = arm_id
        self.information_rights = information_rights

    def input_for(self, task: MethodFacingTask) -> ArmInput:
        return project_task(task, self.information_rights)

    @abstractmethod
    def run(self, task: MethodFacingTask) -> tuple[ProposedMapping, RawOutputRecord]:
        """Return one prediction and one raw-output record, including abstention."""

    @staticmethod
    def abstain(task: MethodFacingTask, *, arm_id: str, model: str = "deterministic") -> tuple[ProposedMapping, RawOutputRecord]:
        return ProposedMapping.abstention(task.case_id), RawOutputRecord(
            arm_id=arm_id,
            model=model,
            case_id=task.case_id,
            prompt_id=None,
            rendered_prompt=None,
            raw_response=None,
            provider="offline",
            latency_ms=0.0,
            outcome="success",
        )
