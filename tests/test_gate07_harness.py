"""Gate 07 baseline interface, rights, and research-router tests."""

from __future__ import annotations

from pathlib import Path

from rag.generation.groq_client import GroqRateLimitError
from rag.generation.provider_router import ProviderRouter
from research.gate07.baselines import BaselineArm, ProposedMapping, project_task
from research.gate07.dataset import build_all_cases
from research.gate07.harness import build_method_facing_task


def test_gate07_rights_projection_removes_unclaimed_information():
    task = build_method_facing_task(build_all_cases()[0])
    projected = project_task(task, frozenset({"new_contracts", "candidate_list"}))
    assert projected.case_id == task.case_id
    assert projected.new_contracts
    assert projected.candidate_new_tool_names
    assert projected.old_contracts == ()
    assert projected.verified_old_traces == ()
    assert projected.task_description is None


def test_gate07_every_arm_interface_can_emit_no_equivalent():
    class AbstainingArm(BaselineArm):
        def run(self, task):
            return self.abstain(task, arm_id=self.arm_id)

    task = build_method_facing_task(next(case for case in build_all_cases() if case.family == "no_equivalent"))
    prediction, raw = AbstainingArm("test_arm", frozenset()).run(task)
    assert prediction.abstain is True
    assert prediction.selected_tool_names == ()
    assert raw.outcome == "success"


def test_gate07_research_router_never_falls_back_to_ollama():
    class FailingGroq:
        model = "model/strong"

        def available(self):
            return True

        def generate_json(self, prompt):
            raise GroqRateLimitError("synthetic 429")

    class SpyOllama:
        model = "qwen3:8b"
        status_calls = 0

        def status(self):
            self.status_calls += 1
            raise AssertionError("research mode touched Ollama")

    router = ProviderRouter(provider="groq", mode="research", groq_client=FailingGroq(), ollama_client=SpyOllama())
    invocation = router.generate_json("synthetic prompt")
    assert invocation.provider == "groq"
    assert invocation.fallback_used is False
    assert invocation.failure_kind == "rate_limited"


def test_gate07_baseline_modules_do_not_import_evaluator_data():
    base = Path(__file__).parents[1] / "research" / "gate07" / "baselines"
    for path in (base / "base.py", base / "models.py"):
        assert "oracle" not in path.read_text(encoding="utf-8").casefold()


def test_gate07_proposed_mapping_supports_many_to_many_predictions():
    mapping = ProposedMapping(
        case_id="G07-G-0001",
        selected_tool_names=("a", "b"),
        ranked_tool_names=("a", "b", "c"),
        argument_pairs=(("old", "x", "a", "x"), ("old", "x", "b", "x")),
    )
    assert len(mapping.selected_tool_names) == 2
    assert len(mapping.argument_pairs) == 2
