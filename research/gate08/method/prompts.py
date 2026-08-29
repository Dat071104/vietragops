"""Versioned Gate 08 signature prompts.

Two prompts, two disjoint information rights. The old-side prompt never sees a
candidate contract; the new-side prompt never sees the old contract, the task
description, or a trace. Keeping them disjoint is what makes the correspondence
in `correspondence.py` a property of the method rather than of the model.
"""

from __future__ import annotations


PROMPT_VERSION = "gate08-signature-v1"

_VOCABULARY = (
    "operation must be one of: create, read, update, delete, check, record, search, other. "
    "Each effect kind must be one of: no_mutation, creates_resource, mutates_field, delete"
    "s_resource. "
    "Each argument value_shape must be one of: opaque_identifier, composite_identifier, "
    "free_text, number, boolean, status_token, date, other. "
    "A concept is the lowercase singular noun for the real-world thing a field refers to, "
    "with no system prefix or suffix: write student, course, term, room, invoice, not "
    "student_id, course_code, term_ref. When the operation's own description names that "
    "thing, use the description's noun in preference to the noun implied by the field name. "
    "If a field carries only one part of a larger composite identifier, set part_of to the "
    "concept of that whole identifier and part_position to prefix or suffix. "
    "If a field carries several concepts joined together, list them in components in the "
    "order they appear. "
    "If the contract text states the exact value this field must take for this operation to "
    "apply, put that value in stated_literal; otherwise use null. "
    "Return JSON only. No markdown, no analysis."
)

_SHAPE = (
    'Return this shape: {{"operation": string, "primary_entity": string, "target_entity": '
    'string or null, "effects": [{{"kind": string, "target_concept": string}}], "arguments": '
    '[{{"name": string, "concept": string, "value_shape": string, "required": boolean, '
    '"part_of": string or null, "part_position": "prefix" or "suffix" or null, "components": '
    '[string], "stated_literal": any or null}}], "output_semantics": [string]}}.'
)

OLD_SIDE_PROMPT = {
    "prompt_id": "gate08-old-signature-v1",
    "version": PROMPT_VERSION,
    "side": "old",
    "information_rights": ["old_contract", "verified_old_traces", "task_description"],
    "text": (
        "You are abstracting the intent of one existing API operation. You are NOT choosing a "
        "replacement and you will not be shown any replacement. Describe only what the "
        "operation below means.\n"
        + _VOCABULARY
        + "\n"
        + _SHAPE
        + "\nEvery entry in arguments must correspond to one field of the operation's input "
        "schema, using that field's exact name.\n\nTASK:\n{task_description}\n\n"
        "OPERATION CONTRACTS:\n{old_contracts}\n\nVERIFIED PAST CALLS:\n{verified_old_traces}\n"
    ),
}

OLD_SIDE_NO_HISTORY_PROMPT = {
    "prompt_id": "gate08-old-signature-no-history-v1",
    "version": PROMPT_VERSION,
    "side": "old",
    "information_rights": ["old_contract", "task_description"],
    "text": (
        "You are abstracting the intent of one existing API operation. You are NOT choosing a "
        "replacement and you will not be shown any replacement. Describe only what the "
        "operation below means.\n"
        + _VOCABULARY
        + "\n"
        + _SHAPE
        + "\nEvery entry in arguments must correspond to one field of the operation's input "
        "schema, using that field's exact name.\n\nTASK:\n{task_description}\n\n"
        "OPERATION CONTRACTS:\n{old_contracts}\n"
    ),
}

OLD_SIDE_TASK_ONLY_PROMPT = {
    "prompt_id": "gate08-old-signature-task-only-v1",
    "version": PROMPT_VERSION,
    "side": "old",
    "information_rights": ["task_description"],
    "text": (
        "You are abstracting the intent of a task that an API operation must accomplish. You "
        "are NOT choosing a replacement and you will not be shown any candidate.\n"
        + _VOCABULARY
        + "\n"
        + _SHAPE
        + "\nYou have no input schema here, so arguments must describe the values the task "
        "itself implies, naming each with the plainest field name you would expect.\n\n"
        "TASK:\n{task_description}\n"
    ),
}

NEW_SIDE_PROMPT = {
    "prompt_id": "gate08-new-signature-v1",
    "version": PROMPT_VERSION,
    "side": "new",
    "information_rights": ["new_contracts"],
    "text": (
        "You are abstracting the intent of one API operation. You are NOT performing a "
        "migration, and you will not be shown any other version of this interface. Describe "
        "only the operation below.\n"
        + _VOCABULARY
        + "\n"
        + _SHAPE
        + "\nEvery entry in arguments must correspond to one field of this operation's input "
        "schema, using that field's exact name.\n\nOPERATION CONTRACT:\n{new_contract}\n"
    ),
}

OLD_SIDE_PROMPTS = {
    "full": OLD_SIDE_PROMPT,
    "no_history": OLD_SIDE_NO_HISTORY_PROMPT,
    "task_only": OLD_SIDE_TASK_ONLY_PROMPT,
}

ALL_PROMPTS = {
    prompt["prompt_id"]: prompt
    for prompt in (
        OLD_SIDE_PROMPT,
        OLD_SIDE_NO_HISTORY_PROMPT,
        OLD_SIDE_TASK_ONLY_PROMPT,
        NEW_SIDE_PROMPT,
    )
}


__all__ = [
    "ALL_PROMPTS",
    "NEW_SIDE_PROMPT",
    "OLD_SIDE_NO_HISTORY_PROMPT",
    "OLD_SIDE_PROMPT",
    "OLD_SIDE_PROMPTS",
    "OLD_SIDE_TASK_ONLY_PROMPT",
    "PROMPT_VERSION",
]
