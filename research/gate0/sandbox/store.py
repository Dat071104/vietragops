"""Deterministic, isolated fictional-education sandbox state (Phase 6.2).

Entirely in-memory: no state ever touches a filesystem path, so it
structurally cannot reach `data/`, the real lifecycle registry, or any
other product path -- there is no path to touch. `reset()` restores the
exact frozen initial fixture every time; `state_hash()` lets a test prove
byte-for-byte reproducibility across repeated resets and process
invocations. All identifiers are synthetic (`CRS-*`, `STU-*`, `PROG-*`,
`TERM-*`) and refer to no real institution, person, or record.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any

_INITIAL_COURSES: dict[str, dict[str, Any]] = {
    "CRS-101": {
        "course_code": "CRS-101",
        "title": "Introduction to Discrete Structures",
        "credits": 3,
        "program": "PROG-CS",
        "seats_available": 5,
    },
    "CRS-201": {
        "course_code": "CRS-201",
        "title": "Data Structures and Algorithms",
        "credits": 4,
        "program": "PROG-CS",
        "seats_available": 0,
    },
    "CRS-301": {
        "course_code": "CRS-301",
        "title": "Educational Policy Seminar",
        "credits": 3,
        "program": "PROG-EDU",
        "seats_available": 3,
    },
}

_INITIAL_PREREQUISITES: dict[str, list[str]] = {
    "CRS-201": ["CRS-101"],
    "CRS-301": [],
}

_INITIAL_SCHEDULES: dict[tuple[str, str], dict[str, Any]] = {
    ("CRS-101", "TERM-2026A"): {"days": ["Mon", "Wed"], "start_time": "08:00", "room": "A101"},
    ("CRS-201", "TERM-2026A"): {"days": ["Tue", "Thu"], "start_time": "10:00", "room": "B203"},
    ("CRS-301", "TERM-2026A"): {"days": ["Fri"], "start_time": "13:00", "room": "C010"},
}

_INITIAL_STUDENT_PROGRAMS: dict[str, str] = {
    "STU-0001": "PROG-CS",
    "STU-0002": "PROG-EDU",
}


class SandboxStateError(RuntimeError):
    """Raised for a sandbox precondition failure (not a Python bug)."""


class EducationSandboxStore:
    """One isolated run's worth of deterministic education-sandbox state."""

    def __init__(self) -> None:
        self._sequence = 0
        self.reset()

    def reset(self) -> None:
        self.courses: dict[str, dict[str, Any]] = deepcopy(_INITIAL_COURSES)
        self.prerequisites: dict[str, list[str]] = deepcopy(_INITIAL_PREREQUISITES)
        self.schedules: dict[tuple[str, str], dict[str, Any]] = deepcopy(_INITIAL_SCHEDULES)
        self.student_programs: dict[str, str] = deepcopy(_INITIAL_STUDENT_PROGRAMS)
        self.enrollments: dict[str, dict[str, Any]] = {}
        self.leave_requests: dict[str, dict[str, Any]] = {}
        self.registrations: dict[str, dict[str, Any]] = {}
        self._sequence = 0

    def next_id(self, prefix: str) -> str:
        self._sequence += 1
        return f"{prefix}-{self._sequence:06d}"

    def state_hash(self) -> str:
        """Deterministic hash of the full mutable state, for reset-reproducibility tests."""
        payload = {
            "courses": self.courses,
            "prerequisites": self.prerequisites,
            "schedules": {f"{code}|{term}": value for (code, term), value in self.schedules.items()},
            "student_programs": self.student_programs,
            "enrollments": self.enrollments,
            "leave_requests": self.leave_requests,
            "registrations": self.registrations,
            "sequence": self._sequence,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"
