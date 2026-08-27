"""In-memory state for the extended fictional education sandbox.

This module deliberately has no filesystem, database, network, or product
imports. A fresh store is deterministic, and ``state_hash`` makes reset and
cross-process reproducibility directly testable.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any


class SandboxStateError(RuntimeError):
    """A real sandbox precondition or domain failure."""


def _courses() -> dict[str, dict[str, Any]]:
    return {
        f"CRS-{index:03d}": {
            "course_code": f"CRS-{index:03d}",
            "title": f"Synthetic Module {index:03d}",
            "credits": 2 + (index % 4),
            "program_code": f"PROG-{(index % 6) + 1:02d}",
            "department": ("COMP", "EDU", "MATH", "LANG")[index % 4],
            "seats_available": 4 + (index % 7),
        }
        for index in range(1, 31)
    }


def _students() -> dict[str, dict[str, str]]:
    return {
        f"STU-{index:04d}": {
            "student_id": f"STU-{index:04d}",
            "display_name": f"Synthetic Learner {index:04d}",
            "program_code": f"PROG-{(index % 6) + 1:02d}",
            "status": "active",
        }
        for index in range(1, 21)
    }


def _rooms() -> dict[str, dict[str, Any]]:
    return {
        f"ROOM-{index:03d}": {
            "room_code": f"ROOM-{index:03d}",
            "building": f"BLDG-{(index % 5) + 1:02d}",
            "capacity": 20 + index,
            "accessible": index % 3 != 0,
        }
        for index in range(1, 16)
    }


def _assessments() -> dict[str, dict[str, Any]]:
    return {
        f"ASM-{index:03d}": {
            "assessment_id": f"ASM-{index:03d}",
            "course_code": f"CRS-{(index % 30) + 1:03d}",
            "assessment_type": ("quiz", "project", "exam")[index % 3],
            "weight": 10 + (index % 5) * 5,
        }
        for index in range(1, 21)
    }


def _invoices() -> dict[str, dict[str, Any]]:
    return {
        f"INV-{index:03d}": {
            "invoice_id": f"INV-{index:03d}",
            "student_id": f"STU-{(index % 20) + 1:04d}",
            "amount": 1000 + index * 25,
            "status": "open" if index % 4 else "paid",
        }
        for index in range(1, 21)
    }


class Gate07SandboxStore:
    """One isolated deterministic run of the Gate 07 fictional API."""

    def __init__(self) -> None:
        self._sequence = 0
        self.reset()

    def reset(self) -> None:
        self.courses = _courses()
        self.students = _students()
        self.rooms = _rooms()
        self.assessments = _assessments()
        self.invoices = _invoices()
        self.schedules = {
            f"CRS-{index:03d}|TERM-{(index % 3) + 1:02d}": {
                "course_code": f"CRS-{index:03d}",
                "term_id": f"TERM-{(index % 3) + 1:02d}",
                "day": ("Mon", "Tue", "Wed", "Thu", "Fri")[index % 5],
                "start_time": f"{8 + (index % 6):02d}:00",
                "room_code": f"ROOM-{(index % 15) + 1:03d}",
            }
            for index in range(1, 31)
        }
        self.enrollments: dict[str, dict[str, Any]] = {}
        self.submissions: dict[str, dict[str, Any]] = {}
        self.payments: dict[str, dict[str, Any]] = {}
        self.credentials: dict[str, dict[str, Any]] = {}
        self.reservations: dict[str, dict[str, Any]] = {}
        self.requests: dict[str, dict[str, Any]] = {}
        self._sequence = 0

    def next_id(self, prefix: str) -> str:
        self._sequence += 1
        return f"{prefix}-{self._sequence:06d}"

    def state_hash(self) -> str:
        payload = {
            "courses": self.courses,
            "students": self.students,
            "rooms": self.rooms,
            "assessments": self.assessments,
            "invoices": self.invoices,
            "schedules": self.schedules,
            "enrollments": self.enrollments,
            "submissions": self.submissions,
            "payments": self.payments,
            "credentials": self.credentials,
            "reservations": self.reservations,
            "requests": self.requests,
            "sequence": self._sequence,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"

    def snapshot(self) -> dict[str, Any]:
        """Return a deep copy for tests; callers cannot mutate live state."""
        return deepcopy(
            {
                "courses": self.courses,
                "students": self.students,
                "rooms": self.rooms,
                "assessments": self.assessments,
                "invoices": self.invoices,
                "schedules": self.schedules,
                "enrollments": self.enrollments,
                "submissions": self.submissions,
                "payments": self.payments,
                "credentials": self.credentials,
                "reservations": self.reservations,
                "requests": self.requests,
                "sequence": self._sequence,
            }
        )
