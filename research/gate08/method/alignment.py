"""Phase 8.4 -- align old arguments onto one candidate's required fields.

Five passes, applied in a fixed order and each one exhausted before the next.
The order is frozen because it is load-bearing: the residual structural pass
must run last, after every declared correspondence and every value the new
contract states for itself has already been consumed.

1. exact concept correspondence            -> identity
2. declared part-of correspondence         -> split
3. declared component correspondence       -> join
4. value stated by the new contract itself -> literal
5. residual conservation of information    -> split or join

Pass 5 is the one that recovers a split or a merge without being told about it:
when one old argument is the only remaining source for exactly two remaining
required fields, its observed value is split; when several old arguments are the
only remaining sources for exactly one remaining required field, they are
joined. Nothing in this module reads a family label, a case id, or an oracle.
"""

from __future__ import annotations

from typing import Any

from research.gate08.method.models import ArgumentAlignment, ArgumentSemantics, IntentSignature
from research.gate08.method.signature import split_composite


# Declared by the method. `join_unresolved` is emitted when a merge is
# structurally certain but its separator is not stated anywhere in the
# information the method is allowed to see. Gate 07's executor has no rule for
# it, so such a case is reported as an unconstructible call rather than being
# completed with an invented separator.
TRANSFORM_KINDS = ("identity", "split", "join", "literal", "split_unresolved", "join_unresolved")


def _by_name(arguments: tuple[ArgumentSemantics, ...]) -> dict[str, ArgumentSemantics]:
    return {argument.name: argument for argument in arguments}


def _first_unused(pool: list[ArgumentSemantics], predicate) -> ArgumentSemantics | None:
    for argument in pool:
        if predicate(argument):
            return argument
    return None


def _identity(old_tool: str, source: ArgumentSemantics, new_tool: str, new_field: str) -> ArgumentAlignment:
    return ArgumentAlignment(
        old_tool=old_tool,
        old_arg=source.name,
        new_tool=new_tool,
        new_arg=new_field,
        value_transform={"kind": "identity"},
        constructed_value=source.observed_value,
        value_resolved=source.observed_value is not None,
    )


def _split(old_tool: str, source: ArgumentSemantics, new_tool: str, new_field: str, position: str) -> ArgumentAlignment:
    parts = split_composite(source.observed_value)
    if parts is None:
        # The separator is only observable in a past call. Without it the
        # correspondence is still reported, but no value is invented.
        return ArgumentAlignment(
            old_tool=old_tool,
            old_arg=source.name,
            new_tool=new_tool,
            new_arg=new_field,
            value_transform={"kind": "split_unresolved", "part": position},
            constructed_value=None,
            value_resolved=False,
        )
    prefix, delimiter, suffix = parts
    return ArgumentAlignment(
        old_tool=old_tool,
        old_arg=source.name,
        new_tool=new_tool,
        new_arg=new_field,
        value_transform={"kind": "split", "delimiter": delimiter, "part": position},
        constructed_value=prefix if position == "prefix" else suffix,
        value_resolved=True,
    )


def _join(
    old_tool: str,
    sources: list[ArgumentSemantics],
    new_tool: str,
    new_field: str,
    delimiter: str | None,
) -> list[ArgumentAlignment]:
    if delimiter is None:
        return [
            ArgumentAlignment(
                old_tool=old_tool,
                old_arg=source.name,
                new_tool=new_tool,
                new_arg=new_field,
                value_transform={"kind": "join_unresolved", "order": index},
                constructed_value=None,
                value_resolved=False,
            )
            for index, source in enumerate(sources)
        ]
    values = [source.observed_value for source in sources]
    resolved = all(value is not None for value in values)
    return [
        ArgumentAlignment(
            old_tool=old_tool,
            old_arg=source.name,
            new_tool=new_tool,
            new_arg=new_field,
            value_transform={"kind": "join", "delimiter": delimiter, "order": index},
            constructed_value=delimiter.join(str(value) for value in values) if resolved else None,
            value_resolved=resolved,
        )
        for index, source in enumerate(sources)
    ]


def _stated_literal(field: ArgumentSemantics | None) -> tuple[bool, Any]:
    """Return the value the new contract states for a field it requires.

    Two sources only: a literal the abstraction found stated in the contract
    text, and the single permitting value of a required boolean gate. Both are
    properties of the new contract; neither consults the old call.
    """
    if field is None:
        return False, None
    if field.stated_literal is not None:
        return True, field.stated_literal
    if field.value_shape == "boolean" and field.required:
        return True, True
    return False, None


def align(
    old: IntentSignature,
    new: IntentSignature,
    new_required_fields: tuple[str, ...],
) -> tuple[tuple[ArgumentAlignment, ...], dict[str, Any], tuple[str, ...], tuple[str, ...]]:
    """Return alignments, constructed values, unmatched new fields, unmatched old args."""
    new_by_name = _by_name(new.arguments)
    pending_fields = [name for name in new_required_fields]
    pool = [argument for argument in old.arguments]
    alignments: list[ArgumentAlignment] = []
    constructed: dict[str, Any] = {}

    def consume(field_name: str, sources: list[ArgumentSemantics], produced: list[ArgumentAlignment]) -> None:
        pending_fields.remove(field_name)
        for source in sources:
            pool.remove(source)
        alignments.extend(produced)
        if produced and all(entry.value_resolved for entry in produced):
            constructed[field_name] = produced[0].constructed_value

    # Pass 1 -- exact concept correspondence.
    for field_name in list(pending_fields):
        field = new_by_name.get(field_name)
        if field is None:
            continue
        source = _first_unused(pool, lambda argument, target=field.concept: argument.concept == target)
        if source is None:
            continue
        consume(field_name, [source], [_identity(old.tool_name, source, new.tool_name, field_name)])

    # Pass 2 -- the new contract declares this field to be part of a whole.
    for field_name in list(pending_fields):
        field = new_by_name.get(field_name)
        if field is None or not field.part_of or field.part_position is None:
            continue
        source = _first_unused(pool, lambda argument, target=field.part_of: argument.concept == target)
        if source is None:
            continue
        consume(field_name, [], [_split(old.tool_name, source, new.tool_name, field_name, field.part_position)])

    # Pass 3 -- the new contract declares this field to be several concepts joined.
    for field_name in list(pending_fields):
        field = new_by_name.get(field_name)
        if field is None or len(field.components) < 2:
            continue
        sources = []
        for component in field.components:
            match = _first_unused(
                [argument for argument in pool if argument not in sources],
                lambda argument, target=component: argument.concept == target,
            )
            if match is None:
                sources = []
                break
            sources.append(match)
        if not sources:
            continue
        consume(field_name, sources, _join(old.tool_name, sources, new.tool_name, field_name, None))

    # Pass 4 -- the new contract states its own value for this field.
    for field_name in list(pending_fields):
        stated, value = _stated_literal(new_by_name.get(field_name))
        if not stated:
            continue
        pending_fields.remove(field_name)
        constructed[field_name] = value

    # Pass 5 -- residual conservation of information.
    if len(pool) == 1 and len(pending_fields) == 2:
        source = pool[0]
        if split_composite(source.observed_value) is not None:
            first, second = pending_fields[0], pending_fields[1]
            produced_first = _split(old.tool_name, source, new.tool_name, first, "prefix")
            produced_second = _split(old.tool_name, source, new.tool_name, second, "suffix")
            alignments.extend([produced_first, produced_second])
            if produced_first.value_resolved:
                constructed[first] = produced_first.constructed_value
            if produced_second.value_resolved:
                constructed[second] = produced_second.constructed_value
            pending_fields.clear()
            pool.clear()
    elif len(pool) >= 2 and len(pending_fields) == 1:
        field_name = pending_fields[0]
        sources = list(pool)
        consume(field_name, sources, _join(old.tool_name, sources, new.tool_name, field_name, None))

    return (
        tuple(alignments),
        constructed,
        tuple(pending_fields),
        tuple(argument.name for argument in pool),
    )


__all__ = ["TRANSFORM_KINDS", "align"]
