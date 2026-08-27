import pytest

from research.gate0.contracts import (
    ContractValidationError,
    Effect,
    Precondition,
    ToolContract,
)


def _base_kwargs(**overrides):
    kwargs = dict(
        tool_id="TOOL_COURSE_LOOKUP",
        version="v1",
        name="search_course",
        description="Look up a course by its code.",
        input_schema={
            "type": "object",
            "properties": {"course_code": {"type": "string"}},
            "required": ["course_code"],
        },
        output_schema={
            "type": "object",
            "properties": {"title": {"type": "string"}, "credits": {"type": "integer"}},
            "required": ["title", "credits"],
        },
        preconditions=(Precondition(kind="resource_exists", target="course_code"),),
        effects=(Effect(kind="no_mutation", target="course_catalog"),),
    )
    kwargs.update(overrides)
    return kwargs


def test_identical_contracts_hash_identically():
    a = ToolContract(**_base_kwargs())
    b = ToolContract(**_base_kwargs())
    assert a.schema_hash == b.schema_hash
    assert a.schema_hash.startswith("sha256:")


def test_description_only_change_does_not_alter_hash():
    a = ToolContract(**_base_kwargs())
    b = ToolContract(**_base_kwargs(description="A completely different description string."))
    assert a.schema_hash == b.schema_hash


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": "find_module"},
        {"input_schema": {"type": "object", "properties": {"course_code": {"type": "integer"}}, "required": ["course_code"]}},
        {"output_schema": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]}},
        {"preconditions": ()},
        {"effects": (Effect(kind="creates_resource", target="enrollment"),)},
    ],
)
def test_meaningful_contract_change_alters_hash(overrides):
    a = ToolContract(**_base_kwargs())
    b = ToolContract(**_base_kwargs(**overrides))
    assert a.schema_hash != b.schema_hash


def test_tool_id_survives_rename_while_hash_changes():
    old = ToolContract(**_base_kwargs())
    renamed = ToolContract(**_base_kwargs(name="find_module"))
    assert old.tool_id == renamed.tool_id
    assert old.schema_hash != renamed.schema_hash


def test_public_view_never_exposes_tool_id():
    contract = ToolContract(**_base_kwargs())
    public = contract.to_public()
    assert not hasattr(public, "tool_id")
    assert "tool_id" not in vars(public)


def test_rejects_bad_tool_id():
    with pytest.raises(ContractValidationError, match="tool_id"):
        ToolContract(**_base_kwargs(tool_id="lower_case_bad"))


def test_rejects_bad_name():
    with pytest.raises(ContractValidationError, match="name"):
        ToolContract(**_base_kwargs(name="Bad-Name"))


def test_rejects_missing_properties():
    with pytest.raises(ContractValidationError, match="properties"):
        ToolContract(**_base_kwargs(input_schema={"type": "object", "properties": {}, "required": []}))


def test_rejects_required_field_not_in_properties():
    with pytest.raises(ContractValidationError, match="required"):
        ToolContract(
            **_base_kwargs(
                input_schema={
                    "type": "object",
                    "properties": {"course_code": {"type": "string"}},
                    "required": ["course_code", "ghost_field"],
                }
            )
        )


def test_rejects_unknown_precondition_kind():
    with pytest.raises(ContractValidationError, match="precondition kind"):
        ToolContract(**_base_kwargs(preconditions=(Precondition(kind="magic", target="course_code"),)))


def test_rejects_precondition_target_not_in_input_or_state():
    with pytest.raises(ContractValidationError, match="Precondition target"):
        ToolContract(**_base_kwargs(preconditions=(Precondition(kind="resource_exists", target="ghost_field"),)))


def test_state_prefixed_precondition_target_is_allowed():
    contract = ToolContract(**_base_kwargs(preconditions=(Precondition(kind="state_flag", target="state:catalog_open"),)))
    assert contract.preconditions[0].target == "state:catalog_open"


def test_rejects_unknown_effect_kind():
    with pytest.raises(ContractValidationError, match="effect kind"):
        ToolContract(**_base_kwargs(effects=(Effect(kind="teleports", target="course_catalog"),)))


def test_rejects_contradictory_effects_on_same_target():
    with pytest.raises(ContractValidationError, match="ambiguous"):
        ToolContract(
            **_base_kwargs(
                effects=(
                    Effect(kind="no_mutation", target="enrollment"),
                    Effect(kind="creates_resource", target="enrollment"),
                )
            )
        )


def test_rejects_non_json_serializable_effect_detail():
    with pytest.raises(ContractValidationError):
        ToolContract(**_base_kwargs(effects=(Effect(kind="creates_resource", target="enrollment", detail={"bad": object()}),)))
