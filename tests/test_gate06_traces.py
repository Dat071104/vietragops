import pytest

from research.gate0.sandbox import EducationSandboxStore
from research.gate0.traces import (
    build_failed_trace_for_version,
    build_verified_traces_for_version,
    replay_trace,
)


@pytest.mark.parametrize("version", ["v1", "v2"])
def test_verified_traces_are_real_successful_executions(version):
    traces = build_verified_traces_for_version(version)
    assert len(traces) == 4
    for trace in traces:
        assert trace.verified is True
        assert trace.error is None
        assert trace.precondition_outcome == "satisfied"
        assert trace.output is not None
        assert trace.schema_hash.startswith("sha256:")


@pytest.mark.parametrize("version", ["v1", "v2"])
def test_verified_traces_have_deterministic_sequence_numbers(version):
    traces = build_verified_traces_for_version(version)
    assert [t.sequence for t in traces] == [1, 2, 3, 4]
    assert len({t.trace_id for t in traces}) == 4


@pytest.mark.parametrize("version", ["v1", "v2"])
def test_replaying_traces_after_reset_reproduces_identical_results(version):
    original = build_verified_traces_for_version(version)

    store = EducationSandboxStore()
    replayed_outputs = []
    replayed_state_hashes = []
    for trace in original:
        assert store.state_hash() == trace.state_hash_before
        output = replay_trace(version, trace, store)
        replayed_outputs.append(output)
        replayed_state_hashes.append(store.state_hash())

    assert replayed_outputs == [t.output for t in original]
    assert replayed_state_hashes == [t.state_hash_after for t in original]


@pytest.mark.parametrize("version", ["v1", "v2"])
def test_failed_trace_is_distinguishable_from_verified_traces(version):
    failed = build_failed_trace_for_version(version)
    assert failed.verified is False
    assert failed.error is not None
    assert failed.precondition_outcome == "violated"
    assert failed.output is None

    verified = build_verified_traces_for_version(version)
    assert all(t.verified is True for t in verified)
    assert failed.trace_id not in {t.trace_id for t in verified}


def test_traces_never_carry_real_provider_or_credential_content():
    for version in ("v1", "v2"):
        for trace in build_verified_traces_for_version(version):
            blob = repr(trace)
            for banned in ("groq", "GROQ_API_KEY", "sk-", "Bearer "):
                assert banned.lower() not in blob.lower()
