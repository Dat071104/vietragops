import pytest

from research.gate0.sandbox import (
    VERSIONS,
    EducationSandboxStore,
    SandboxStateError,
    build_api,
)


@pytest.mark.parametrize("version", VERSIONS)
def test_reset_is_byte_for_byte_reproducible(version):
    store = EducationSandboxStore()
    api = build_api(version, store)
    initial_hash = store.state_hash()

    # Mutate, then reset -- state hash must return to the exact initial value.
    _mutate(version, api)
    assert store.state_hash() != initial_hash
    store.reset()
    assert store.state_hash() == initial_hash


def _mutate(version, api):
    if version == "v1":
        api.create_enrollment(student_id="STU-0001", course_code="CRS-101", semester="TERM-2026A")
    elif version == "v2":
        api.create_enrollment(student_id="STU-0001", course_code="CRS-101", semester="TERM-2026A", consent_ack=True)
    else:
        api.finalize_registration(learner_ref="STU-0001", section_code="CRS-101::TERM-2026A", payment_status="paid")


@pytest.mark.parametrize("version", VERSIONS)
def test_repeated_reset_plus_identical_inputs_are_deterministic(version):
    results = []
    for _ in range(3):
        store = EducationSandboxStore()
        api = build_api(version, store)
        if version == "v1":
            out = api.search_course(course_code="CRS-101")
        elif version == "v2":
            out = api.find_module(course_code="CRS-101")
        else:
            out = api.find_module(course_code="CRS-101")
        results.append((out, store.state_hash()))
    assert results[0] == results[1] == results[2]


def test_sandbox_state_never_touches_a_filesystem_path():
    import research.gate0.sandbox.store as store_module

    source = open(store_module.__file__, encoding="utf-8").read()
    for banned in ("open(", "Path(", "os.path", "sqlite3", "requests.", "httpx."):
        assert banned not in source, f"sandbox store must never touch the filesystem or network, found {banned!r}"


def test_v1_precondition_failure_is_real_not_metadata_only():
    store = EducationSandboxStore()
    api = build_api("v1", store)
    with pytest.raises(SandboxStateError, match="Unknown course_code"):
        api.search_course(course_code="CRS-999")


def test_v1_enrollment_effect_is_real_seat_decrement():
    store = EducationSandboxStore()
    api = build_api("v1", store)
    before = store.courses["CRS-101"]["seats_available"]
    api.create_enrollment(student_id="STU-0001", course_code="CRS-101", semester="TERM-2026A")
    assert store.courses["CRS-101"]["seats_available"] == before - 1
    assert len(store.enrollments) == 1


def test_v1_enrollment_precondition_blocks_when_no_seats():
    store = EducationSandboxStore()
    api = build_api("v1", store)
    with pytest.raises(SandboxStateError, match="No seats available"):
        api.create_enrollment(student_id="STU-0001", course_code="CRS-201", semester="TERM-2026A")


def test_v2_added_required_field_is_enforced_by_real_execution():
    store = EducationSandboxStore()
    api = build_api("v2", store)
    with pytest.raises(TypeError):
        api.create_enrollment(student_id="STU-0001", course_code="CRS-101", semester="TERM-2026A")  # missing consent_ack
    with pytest.raises(SandboxStateError, match="consent_ack must be true"):
        api.create_enrollment(student_id="STU-0001", course_code="CRS-101", semester="TERM-2026A", consent_ack=False)


def test_v2_output_restructure_is_real():
    store = EducationSandboxStore()
    v1_api = build_api("v1", store)
    v1_out = v1_api.get_timetable(course_code="CRS-101", semester="TERM-2026A")
    assert v1_out == {"days": ["Mon", "Wed"], "start_time": "08:00", "room": "A101"}

    store.reset()
    v2_api = build_api("v2", store)
    v2_out = v2_api.get_timetable(course_code="CRS-101", semester="TERM-2026A")
    assert v2_out == {"schedule": {"days": ["Mon", "Wed"], "start_time": "08:00", "location": {"room": "A101"}}}


def test_v3_argument_split_reconstructs_the_same_course():
    store = EducationSandboxStore()
    api = build_api("v3", store)
    out = api.check_prerequisite(program_code="PROG-CS", subject_area="CRS", catalog_number="201")
    assert out == {"eligible": True, "missing": []}
    with pytest.raises(SandboxStateError, match="Unknown course"):
        api.check_prerequisite(program_code="PROG-CS", subject_area="CRS", catalog_number="999")


def test_v3_argument_merge_reconstructs_the_same_section():
    store = EducationSandboxStore()
    api = build_api("v3", store)
    out = api.get_timetable(section_code="CRS-101::TERM-2026A")
    assert out == {"schedule": {"days": ["Mon", "Wed"], "start_time": "08:00", "location": {"room": "A101"}}}
    with pytest.raises(SandboxStateError, match="No schedule"):
        api.get_timetable(section_code="CRS-999::TERM-2026A")


def test_v3_tool_replacement_requires_payment_precondition():
    store = EducationSandboxStore()
    api = build_api("v3", store)
    with pytest.raises(SandboxStateError, match="payment_status must be 'paid'"):
        api.finalize_registration(learner_ref="STU-0001", section_code="CRS-101::TERM-2026A", payment_status="unpaid")
    result = api.finalize_registration(learner_ref="STU-0001", section_code="CRS-101::TERM-2026A", payment_status="paid")
    assert result["status"] == "registered"
    assert store.courses["CRS-101"]["seats_available"] == 4


def test_v3_near_collision_tools_have_distinct_effects():
    store = EducationSandboxStore()
    api = build_api("v3", store)
    exact = api.find_module(course_code="CRS-101")
    assert "title" in exact and "matches" not in exact

    fuzzy = api.browse_catalog(query_text="discrete")
    assert "matches" in fuzzy
    assert any(m["course_code"] == "CRS-101" for m in fuzzy["matches"])


def test_no_equivalent_tool_absent_from_v2_and_v3():
    v2_names = {c.name for c in build_api("v2", EducationSandboxStore()).contracts()}
    v3_names = {c.name for c in build_api("v3", EducationSandboxStore()).contracts()}
    assert "submit_leave_request" not in v2_names
    assert "submit_leave_request" not in v3_names
    assert not hasattr(build_api("v2", EducationSandboxStore()), "submit_leave_request")
    assert not hasattr(build_api("v3", EducationSandboxStore()), "submit_leave_request")


def test_tool_replacement_genuinely_changes_identity_unlike_a_rename():
    v2_contracts = {c.name: c for c in build_api("v2", EducationSandboxStore()).contracts()}
    v3_contracts = {c.name: c for c in build_api("v3", EducationSandboxStore()).contracts()}
    old_enrollment = v2_contracts["create_enrollment"]
    new_registration = v3_contracts["finalize_registration"]
    assert old_enrollment.tool_id != new_registration.tool_id, (
        "A genuine replacement must not share tool_id with what it replaces -- "
        "otherwise it would be indistinguishable from a rename."
    )
    # Contrast: find_module is carried forward unchanged and DOES keep its identity.
    assert v2_contracts["find_module"].tool_id == v3_contracts["find_module"].tool_id


def test_each_version_contracts_are_internally_consistent():
    for version in VERSIONS:
        contracts = build_api(version, EducationSandboxStore()).contracts()
        assert contracts, f"{version} must declare at least one contract"
        for contract in contracts:
            assert contract.version == version
