"""Rule-ablation harness for the Gate 19 oracle-reachability auditor.

Two questions are answered here, both raised against manuscript version 2.

1. The committed auditor evaluates a reachability rule, ``visible_literal``,
   that the frozen rights declaration does not list. Does the headline
   50/310 result depend on it? This module re-runs the 310-item register
   under four rule configurations and reports whether the classification
   counts move.

2. The external 20-pair sample is accepted partly through a hand-supplied
   observability annotation. How much of 20/20 survives if that annotation
   is withheld and only mechanical rules are allowed?

The auditor itself is not modified. This module re-implements the decision
chain with switches and asserts that the default configuration reproduces
``research.gate19.auditor.classify_item`` item for item, so an ablation
result cannot drift away from the artifact it is meant to describe.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any, Iterable

from research.gate19.auditor import (
    CONVENTION_UNOBSERVABLE,
    REACHABLE,
    TARGET_ABSENT,
    _as_text,
    _fields_for_tool,
    _find_hidden_join,
    _source_values,
    _visible_split,
    _visible_text,
    build_gate07_items,
    classify_item,
)
from research.gate19.external_audit import build_audit_input


LITERAL_SCOPES = ("visible_text", "source_values")


def classify_variant(
    item: dict[str, Any],
    *,
    use_visible_literal: bool = True,
    split_before_literal: bool = False,
    literal_scope: str = "visible_text",
    allow_declared_external: bool = True,
) -> tuple[str, str | None]:
    """Classify one item under a rule configuration; return (status, rule_id)."""

    if literal_scope not in LITERAL_SCOPES:
        raise ValueError(f"literal_scope must be one of {LITERAL_SCOPES}")

    fields = _fields_for_tool(item, item["new_tool"])
    target_value = item.get("target_value")
    source_values = _source_values(item)
    visible_text = _visible_text(item)

    if item["new_arg"] not in fields:
        return TARGET_ABSENT, "target_field_undeclared"
    if target_value is None:
        return TARGET_ABSENT, "target_value_absent"

    target_text = _as_text(target_value)
    if target_text in source_values:
        return REACHABLE, "identity"

    def literal() -> str | None:
        if not (use_visible_literal and isinstance(target_value, str) and target_value):
            return None
        surface = visible_text if literal_scope == "visible_text" else "\n".join(source_values)
        return "visible_literal" if target_value in surface else None

    def split() -> str | None:
        return "visible_split" if _visible_split(target_text, source_values) is not None else None

    def join() -> str | None:
        return "unobservable_join" if _find_hidden_join(target_text, source_values, visible_text) is not None else None

    # The committed order is literal, then join, then split. V3 swaps the
    # first two reachability rules to show the classification is insensitive
    # to which of the co-extensive rules is consulted first.
    if split_before_literal:
        chain = (split, literal, join)
    else:
        chain = (literal, join, split)

    for rule in chain:
        hit = rule()
        if hit == "unobservable_join":
            return CONVENTION_UNOBSERVABLE, hit
        if hit is not None:
            return REACHABLE, hit

    external = item.get("derivation")
    if allow_declared_external and isinstance(external, dict) and external.get("status") == "observable":
        return REACHABLE, "declared_external_derivation"

    return CONVENTION_UNOBSERVABLE, "fail_closed"


def _summarize(items: Iterable[dict[str, Any]], **config: Any) -> dict[str, Any]:
    statuses: Counter[str] = Counter()
    rules: Counter[str] = Counter()
    families: dict[str, Counter[str]] = defaultdict(Counter)
    for item in items:
        status, rule = classify_variant(item, **config)
        statuses[status] += 1
        rules[rule or "<none>"] += 1
        families[item.get("family") or "<unknown>"][status] += 1
    total = sum(statuses.values())
    return {
        "config": config,
        "item_count": total,
        "status_counts": {
            REACHABLE: statuses[REACHABLE],
            TARGET_ABSENT: statuses[TARGET_ABSENT],
            CONVENTION_UNOBSERVABLE: statuses[CONVENTION_UNOBSERVABLE],
        },
        "unreachable_total": statuses[TARGET_ABSENT] + statuses[CONVENTION_UNOBSERVABLE],
        "rule_fire_counts": dict(sorted(rules.items())),
        "families": {
            family: {
                "pairs": sum(counts.values()),
                "unreachable": counts[TARGET_ABSENT] + counts[CONVENTION_UNOBSERVABLE],
            }
            for family, counts in sorted(families.items())
        },
    }


def verify_default_matches_auditor(items: list[dict[str, Any]], rights: dict[str, Any]) -> int:
    """Assert the default variant reproduces the committed auditor exactly."""

    mismatches = 0
    for item in items:
        status, _rule = classify_variant(item)
        if status != classify_item(item, rights)["status"]:
            mismatches += 1
    if mismatches:
        raise AssertionError(
            f"ablation default configuration disagrees with the committed auditor on {mismatches} items"
        )
    return len(items)


VARIANTS = {
    "V1_baseline": {},
    "V2_no_visible_literal": {"use_visible_literal": False},
    "V3_split_before_literal": {"split_before_literal": True},
    "V4_literal_source_values_only": {"literal_scope": "source_values"},
}


def build(repo_root: Path) -> dict[str, Any]:
    rights = json.loads((repo_root / "research/gate19/information_rights.json").read_text(encoding="utf-8"))
    grammar_path = repo_root / "research/gate19/derivation_grammar.json"
    grammar = json.loads(grammar_path.read_text(encoding="utf-8"))

    items = build_gate07_items()
    checked = verify_default_matches_auditor(items, rights)

    synthetic = {name: _summarize(items, **config) for name, config in VARIANTS.items()}
    baseline = synthetic["V1_baseline"]["status_counts"]
    invariant = all(v["status_counts"] == baseline for v in synthetic.values())

    register = json.loads((repo_root / "gates/baselines/GATE_19_EXTERNAL_MCP_PAIRS.json").read_text(encoding="utf-8"))
    external_items = build_audit_input(register)
    external = {
        "with_hand_annotation": _summarize(external_items, allow_declared_external=True),
        "without_hand_annotation": _summarize(external_items, allow_declared_external=False),
    }

    return {
        "schema": "gate22.rule_ablation.v1",
        "purpose": (
            "Establish whether the headline 50/310 unreachability result depends on visible_literal, "
            "a reachability rule the frozen rights declaration does not list, and how much of the "
            "external 20/20 result is mechanical rather than hand-adjudicated."
        ),
        "grammar_declaration": "research/gate19/derivation_grammar.json",
        "grammar_schema": grammar["schema"],
        "rights_schema": rights["schema"],
        "auditor_agreement_items_checked": checked,
        "synthetic_register": synthetic,
        "synthetic_headline_invariant": invariant,
        "external_sample": external,
        "external_reading": (
            "Withholding the hand annotation leaves 5 of 20 pairs reachable by mechanical rule and "
            "classifies 15 fail-closed. The 20/20 figure therefore records the adjudicator's judgement "
            "for three quarters of the sample and is not an independent specificity estimate."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--repo-root", default=None, help="Repository root; defaults to this file's repository")
    args = parser.parse_args()

    repo_root = Path(args.repo_root) if args.repo_root else Path(__file__).resolve().parents[2]
    result = build(repo_root)

    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(
        {
            "output": target.as_posix(),
            "synthetic_headline_invariant": result["synthetic_headline_invariant"],
            "variants": {k: v["status_counts"] for k, v in result["synthetic_register"].items()},
            "external_without_annotation": result["external_sample"]["without_hand_annotation"]["status_counts"],
        },
        ensure_ascii=True, sort_keys=True, indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
