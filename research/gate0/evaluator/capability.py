"""The evaluator-only capability token (Phase 6.4/6.6).

`EvaluatorCapability` is a real, importable Python class -- constructing
one is not cryptographically restricted, and a repository owner can
always do so. Its purpose is narrower: it makes every oracle read require
an explicit capability argument, so an oracle accessor cannot be called
by accident from code that was never handed one, and it gives
`tests/test_gate06_oracle_boundary.py` a single, greppable class name to
prove the method-facing harness never imports or constructs.
"""

from __future__ import annotations


class EvaluatorCapability:
    __slots__ = ()
