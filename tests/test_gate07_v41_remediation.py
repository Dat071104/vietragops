"""V4.1 regression tests for bounded throttling, provider metadata, and usage."""

from __future__ import annotations

import io
import json
from pathlib import Path
from types import SimpleNamespace
from urllib import error

import pytest

from rag.generation.groq_client import GroqClient
from rag.generation.provider_router import ProviderInvocation, ProviderRouter
from research.gate07.runner import llm
from research.gate07.runner.rate_ledger import RateLimitLedger, RateLimits


def _limits(**overrides):
    base = {"rpm": 100, "tpm": 100_000, "rpd": 100, "tpd": 100_000}
    return RateLimits(
        per_key=dict(base),
        pool={**base, **overrides.get("pool", {})},
        org={**base, **overrides.get("org", {})},
        reserve_fraction=0.0,
    )


def _run_args(tmp_path: Path):
    return SimpleNamespace(
        tasks="unused",
        output=str(tmp_path / "results.jsonl"),
        raw=str(tmp_path / "raw.jsonl"),
        ledger=str(tmp_path / "router.sqlite3"),
        request_ledger=str(tmp_path / "requests.jsonl"),
        models="openai/gpt-oss-120b,openai/gpt-oss-20b",
        preflight_only=False,
        protocol="protocol.json",
    )


def test_bug1_failed_rows_are_not_resume_cached(tmp_path: Path):
    output = tmp_path / "results.jsonl"
    failed = {"arm_id": "arm", "model": "model", "case_id": "case-1", "prompt_id": "prompt", "outcome": "provider_failure"}
    success = {"arm_id": "arm", "model": "model", "case_id": "case-2", "prompt_id": "prompt", "outcome": "success"}
    output.write_text("\n".join(json.dumps(row) for row in (failed, success)) + "\n", encoding="utf-8")

    assert llm._load_cache(output) == {("arm", "model", "case-2", "prompt")}


def test_bug1_rejected_request_waits_retries_and_is_not_recorded(monkeypatch, tmp_path: Path):
    class FakeLedger:
        instances = []

        def __init__(self, *args, **kwargs):
            self.allow_calls = 0
            self.wait_calls = 0
            self.records = []
            FakeLedger.instances.append(self)

        def allow(self, input_tokens, output_tokens):
            self.allow_calls += 1
            return (self.allow_calls >= 2, None if self.allow_calls >= 2 else "pool_rpm")

        def wait_time(self, input_tokens, output_tokens):
            self.wait_calls += 1
            return 0.25

        def record(self, **kwargs):
            self.records.append(kwargs)

        def close(self):
            pass

    router_calls = []

    class FakeRouter:
        def __init__(self, **kwargs):
            pass

        def generate_json(self, prompt, **kwargs):
            router_calls.append(kwargs)
            return ProviderInvocation(
                provider="groq",
                model=kwargs.get("model", "openai/gpt-oss-120b"),
                payload={"ok": True},
                usage={"input_tokens_actual": 123, "output_tokens_actual": 37, "total_tokens_actual": 160},
            )

    sleeps = []
    monkeypatch.setattr(llm, "RateLimitLedger", FakeLedger)
    monkeypatch.setattr(llm, "ProviderRouter", FakeRouter)
    monkeypatch.setattr(llm, "GroqClient", lambda **kwargs: object())
    monkeypatch.setattr(llm, "preflight_headline_run", lambda path: {"status": "passed"})
    monkeypatch.setattr(llm, "load_public_tasks", lambda path: [{"case_id": "case-1"}])
    monkeypatch.setattr(llm, "render_llm_prompt", lambda arm_id, task: ("prompt", "synthetic prompt"))
    monkeypatch.setattr(llm, "parse_llm_payload", lambda payload, task: payload)
    monkeypatch.setattr(llm, "_ordered_arm_models", lambda models: (("llm_old_new_direct", models[0]),))
    monkeypatch.setattr(llm.time, "sleep", sleeps.append)
    monkeypatch.setattr(llm, "_args", lambda: _run_args(tmp_path))

    llm.run()

    ledger = FakeLedger.instances[-1]
    assert ledger.allow_calls == 2
    assert ledger.wait_calls == 1
    assert sleeps == [0.25]
    assert len(ledger.records) == 1
    assert ledger.records[0]["input_tokens"] == 123
    assert ledger.records[0]["output_tokens"] == 37
    assert router_calls[0]["max_tokens"] == 1536
    result = json.loads((tmp_path / "results.jsonl").read_text(encoding="utf-8"))
    assert result["token_usage"]["output_tokens_actual"] == 37


def test_bug1_fifth_throttle_check_is_typed_and_retryable(monkeypatch, tmp_path: Path):
    class FakeLedger:
        instance = None

        def __init__(self, *args, **kwargs):
            self.allow_calls = 0
            self.records = []
            FakeLedger.instance = self

        def allow(self, input_tokens, output_tokens):
            self.allow_calls += 1
            return False, "pool_rpm"

        def wait_time(self, input_tokens, output_tokens):
            return 0.0

        def record(self, **kwargs):
            self.records.append(kwargs)

        def close(self):
            pass

    class FailingIfCalledRouter:
        def __init__(self, **kwargs):
            pass

        def generate_json(self, prompt, **kwargs):
            pytest.fail("provider must not be called after client throttling")

    sleeps = []
    monkeypatch.setattr(llm, "RateLimitLedger", FakeLedger)
    monkeypatch.setattr(llm, "ProviderRouter", FailingIfCalledRouter)
    monkeypatch.setattr(llm, "GroqClient", lambda **kwargs: object())
    monkeypatch.setattr(llm, "preflight_headline_run", lambda path: {"status": "passed"})
    monkeypatch.setattr(llm, "load_public_tasks", lambda path: [{"case_id": "case-1"}])
    monkeypatch.setattr(llm, "render_llm_prompt", lambda arm_id, task: ("prompt", "synthetic prompt"))
    monkeypatch.setattr(llm, "_ordered_arm_models", lambda models: (("llm_old_new_direct", models[0]),))
    monkeypatch.setattr(llm.time, "sleep", sleeps.append)
    monkeypatch.setattr(llm, "_args", lambda: _run_args(tmp_path))

    llm.run()

    assert FakeLedger.instance.allow_calls == 5
    assert sleeps == [0.0, 0.0, 0.0, 0.0]
    assert FakeLedger.instance.records == []
    result = json.loads((tmp_path / "results.jsonl").read_text(encoding="utf-8"))
    assert result["failure_kind"] == "client_throttled"
    assert llm._load_cache(tmp_path / "results.jsonl") == set()


def test_rate_ledger_wait_time_is_read_only(monkeypatch, tmp_path: Path):
    now = 1_000.0
    monkeypatch.setattr("research.gate07.runner.rate_ledger.time.time", lambda: now)
    ledger = RateLimitLedger(
        tmp_path / "router.sqlite3",
        tmp_path / "requests.jsonl",
        _limits(pool={"rpm": 1}),
    )
    ledger.record(arm_id="arm", model="model", case_id="case", input_tokens=10, output_tokens=20, outcome="success")

    allowed, reason = ledger.allow(1, 1)
    wait = ledger.wait_time(1, 1)
    assert allowed is False and reason == "pool_rpm"
    assert wait == pytest.approx(60.001)
    assert len((tmp_path / "requests.jsonl").read_text(encoding="utf-8").splitlines()) == 1
    ledger.close()


def test_bug2_http_error_body_is_exposed_without_breaking_research_policy(monkeypatch):
    body = b'{"error":{"message":"invalid_request_error"}}'

    def _urlopen(raw_req, timeout):
        raise error.HTTPError(raw_req.full_url, 400, "Bad Request", {}, io.BytesIO(body))

    monkeypatch.setattr("urllib.request.urlopen", _urlopen)
    client = GroqClient(api_keys=["key"], max_retries=0)
    invocation = ProviderRouter(provider="groq", mode="research", groq_client=client).generate_json("hello")

    assert invocation.payload is None
    assert invocation.failure_kind == "provider_error"
    assert invocation.provider_error_body == body.decode("utf-8")
    assert client.last_provider_error_body == body.decode("utf-8")


def test_bug4_usage_is_taken_from_provider_body_and_returned_as_metadata(monkeypatch):
    response_body = {
        "choices": [{"message": {"content": json.dumps({"answer": "ok"})}}],
        "usage": {"prompt_tokens": 111, "completion_tokens": 29, "total_tokens": 140},
    }

    class MockResponse:
        def read(self):
            return json.dumps(response_body).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

    monkeypatch.setattr("urllib.request.urlopen", lambda raw_req, timeout: MockResponse())
    client = GroqClient(api_keys=["key"], max_retries=0)
    result = client.generate_json("hello")
    invocation = ProviderRouter(provider="groq", mode="research", groq_client=client).generate_json("hello")

    assert result == {"answer": "ok"}
    assert client.last_usage == {"input_tokens_actual": 111, "output_tokens_actual": 29, "total_tokens_actual": 140}
    assert invocation.usage == client.last_usage


def test_s26_execution_order_is_fixed_but_not_nested_default_order():
    models = ("openai/gpt-oss-120b", "openai/gpt-oss-20b")
    first = llm._ordered_arm_models(models)
    second = llm._ordered_arm_models(models)
    assert first == second
    assert set(first) == {(arm_id, model) for arm_id in llm.ARM_IDS for model in models}
    assert first != tuple((arm_id, model) for model in models for arm_id in llm.ARM_IDS)


def test_cost_budget_reserves_maximum_and_settles_actual_usage(tmp_path: Path):
    budget = llm.CostBudget(tmp_path / "results.jsonl")
    allowed, reservation = budget.reserve("openai/gpt-oss-120b", 1_000, 1_536)
    assert allowed is True
    cost, usage_complete = budget.settle(
        reservation,
        "openai/gpt-oss-120b",
        {"input_tokens_actual": 100, "output_tokens_actual": 20},
        billable=True,
    )
    assert usage_complete is True
    assert cost == pytest.approx((100 * 0.15 + 20 * 0.60) / 1_000_000)
    assert budget.spent_usd == pytest.approx(cost)

    tiny_budget = llm.CostBudget(tmp_path / "other.jsonl", cap_usd=0.000001)
    allowed, _ = tiny_budget.reserve("openai/gpt-oss-120b", 1_000, 1_536)
    assert allowed is False
