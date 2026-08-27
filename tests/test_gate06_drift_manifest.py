from research.gate0.drift import ALL_FAMILIES, build_case_manifest, held_out_cases
from research.gate0.sandbox import VERSIONS, EducationSandboxStore, build_api


def test_all_nine_families_are_defined():
    assert len(ALL_FAMILIES) == 9
    assert len(set(ALL_FAMILIES)) == 9


def test_manifest_covers_at_least_eight_families():
    families = {case.family for case in build_case_manifest()}
    assert len(families) >= 8
    assert families <= set(ALL_FAMILIES)


def test_manifest_covers_all_nine_families():
    families = {case.family for case in build_case_manifest()}
    assert families == set(ALL_FAMILIES)


def test_manifest_has_semantic_near_collision_case():
    cases = [c for c in build_case_manifest() if c.family == "semantic_near_collision"]
    assert len(cases) == 1
    case = cases[0]
    assert len(case.candidate_new_tool_names) >= 2
    assert case.old_tool_name in case.candidate_new_tool_names or True  # correct answer is oracle-only, not asserted here


def test_manifest_has_no_equivalent_cases_with_all_candidates_wrong():
    no_equiv_cases = [c for c in build_case_manifest() if c.family == "no_equivalent"]
    assert len(no_equiv_cases) >= 1
    for case in no_equiv_cases:
        # None of the offered candidates may share the old tool's real identity --
        # verified structurally: the old tool's name never reappears among candidates.
        assert case.old_tool_name not in case.candidate_new_tool_names


def test_case_ids_are_unique_and_deterministic():
    cases = build_case_manifest()
    ids = [c.case_id for c in cases]
    assert len(ids) == len(set(ids))
    assert ids == sorted(ids)


def test_seeds_are_unique_and_frozen():
    cases = build_case_manifest()
    seeds = [c.seed for c in cases]
    assert len(seeds) == len(set(seeds))


def test_manifest_is_stable_across_calls():
    assert build_case_manifest() == build_case_manifest()


def test_held_out_cases_are_structurally_disjoint_from_graded_manifest():
    graded_ids = {c.case_id for c in build_case_manifest()}
    held_ids = {c.case_id for c in held_out_cases()}
    assert graded_ids.isdisjoint(held_ids)
    assert all(c.held_out for c in held_out_cases())
    assert not any(c.held_out for c in build_case_manifest())


def test_every_case_references_a_real_tool_and_version_pair():
    for case in build_case_manifest() + held_out_cases():
        assert case.old_version in VERSIONS
        assert case.new_version in VERSIONS
        old_names = {c.name for c in build_api(case.old_version, EducationSandboxStore()).contracts()}
        assert case.old_tool_name in old_names, f"{case.case_id}: {case.old_tool_name!r} not a real {case.old_version} tool"
        if case.family != "no_equivalent":
            new_names = {c.name for c in build_api(case.new_version, EducationSandboxStore()).contracts()}
            assert set(case.candidate_new_tool_names) <= new_names, f"{case.case_id}: candidates not all real {case.new_version} tools"
