"""Deterministic lexical, embedding, and cross-encoder scoring functions."""

from __future__ import annotations

import importlib
import json
import re
from typing import Any, Callable


def _tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", value.casefold()) if token}


def _contract_text(contract: dict[str, Any], *, names_and_description: bool, names_only: bool = False) -> str:
    if names_only:
        return contract.get("name", "")
    if names_and_description:
        return " ".join((contract.get("name", ""), contract.get("description", "")))
    return json.dumps(
        {
            "input_schema": contract.get("input_schema", {}),
            "output_schema": contract.get("output_schema", {}),
            "preconditions": contract.get("preconditions", []),
            "effects": contract.get("effects", []),
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


def _jaccard(left: str, right: str) -> float:
    a, b = _tokens(left), _tokens(right)
    if not a and not b:
        return 1.0
    return len(a & b) / max(1, len(a | b))


def _old_text(task: dict[str, Any], *, names_and_description: bool, names_only: bool = False) -> str:
    return " ".join(_contract_text(contract, names_and_description=names_and_description, names_only=names_only) for contract in task["old_contracts"])


def _candidate_scores(task: dict[str, Any], scorer: Callable[[str, str], float], *, names_and_description: bool, names_only: bool = False) -> list[tuple[str, float]]:
    old_text = _old_text(task, names_and_description=names_and_description, names_only=names_only)
    return [(contract["name"], scorer(old_text, _contract_text(contract, names_and_description=names_and_description, names_only=names_only))) for contract in task["new_contracts"]]


def _field_names(contract: dict[str, Any]) -> tuple[str, ...]:
    return tuple(contract.get("input_schema", {}).get("properties", {}).keys())


def _field_pairs(task: dict[str, Any], selected: tuple[str, ...]) -> tuple[tuple[str, str, str, str], ...]:
    contracts = {contract["name"]: contract for contract in task["new_contracts"]}
    pairs: list[tuple[str, str, str, str]] = []
    for old_contract in task["old_contracts"]:
        old_fields = _field_names(old_contract)
        for new_name in selected:
            new_fields = _field_names(contracts[new_name])
            for old_field in old_fields:
                if not new_fields:
                    continue
                best = max(new_fields, key=lambda field: _jaccard(old_field, field))
                if _jaccard(old_field, best) > 0.0 or len(new_fields) == 1:
                    pairs.append((old_contract["name"], old_field, new_name, best))
    return tuple(pairs)


def _v4_prediction(task: dict[str, Any], selected: tuple[str, ...], ranked: tuple[str, ...], pairs: tuple[tuple[str, str, str, str], ...]) -> dict[str, Any]:
    mapping = [
        {
            "old_tool": old_tool,
            "old_arg": old_arg,
            "new_tool": new_tool,
            "new_arg": new_arg,
            "value_transform": {"kind": "identity"},
        }
        for old_tool, old_arg, new_tool, new_arg in pairs
    ]
    return {
        "selected_tool_names": list(selected),
        "best_candidate_tool_names": list(selected),
        "ranked_tool_names": list(ranked),
        "argument_pairs": [list(pair) for pair in pairs],
        "argument_mapping": mapping,
        "value_transforms": [entry["value_transform"] for entry in mapping],
        "constructed_argument_values": [],
        "equivalence_verdict": "equivalent",
        "confidence": 1.0,
        "abstain": False,
        "selection_contract": "v4_forced",
    }


def predict_lexical(task: dict[str, Any], *, names_only: bool) -> tuple[dict[str, Any], list[tuple[str, float]]]:
    scores = _candidate_scores(task, _jaccard, names_and_description=False, names_only=names_only)
    ranked = tuple(name for name, _ in sorted(scores, key=lambda pair: (-pair[1], pair[0])))
    selected = ranked[:1]
    return _v4_prediction(task, selected, ranked, _field_pairs(task, selected)), scores


def _load_sentence_transformer(model_path: str):
    module = importlib.import_module("sentence_transformers")
    model_cls = getattr(module, "SentenceTransformer")
    return model_cls(model_path, device="cpu", local_files_only=True)


def _load_cross_encoder(model_path: str):
    module = importlib.import_module("sentence_transformers")
    model_cls = getattr(module, "CrossEncoder")
    return model_cls(model_path, device="cpu", local_files_only=True)


def predict_embedding(task: dict[str, Any], model: Any, *, names_and_description: bool) -> tuple[dict[str, Any], list[tuple[str, float]]]:
    old_text = _old_text(task, names_and_description=names_and_description)
    candidates = [_contract_text(contract, names_and_description=names_and_description) for contract in task["new_contracts"]]
    vectors = model.encode([old_text, *candidates], normalize_embeddings=True)
    scores = [(contract["name"], float(vectors[0] @ vectors[index + 1])) for index, contract in enumerate(task["new_contracts"])]
    ranked = tuple(name for name, _ in sorted(scores, key=lambda pair: (-pair[1], pair[0])))
    selected = ranked[:1]
    return _v4_prediction(task, selected, ranked, _field_pairs(task, selected)), scores


def predict_cross_encoder(task: dict[str, Any], model: Any) -> tuple[dict[str, Any], list[tuple[str, float]]]:
    old_text = _old_text(task, names_and_description=False)
    pairs = [(old_text, _contract_text(contract, names_and_description=False)) for contract in task["new_contracts"]]
    values = model.predict(pairs, show_progress_bar=False)
    scores = [(contract["name"], float(values[index])) for index, contract in enumerate(task["new_contracts"])]
    ranked = tuple(name for name, _ in sorted(scores, key=lambda pair: (-pair[1], pair[0])))
    selected = ranked[:1]
    return _v4_prediction(task, selected, ranked, _field_pairs(task, selected)), scores


def _prediction_from_scores(task: dict[str, Any], scores: list[tuple[str, float]]) -> dict[str, Any]:
    ranked = tuple(name for name, _ in sorted(scores, key=lambda pair: (-pair[1], pair[0])))
    selected = ranked[:1]
    return _v4_prediction(task, selected, ranked, _field_pairs(task, selected))


def predict_embedding_batch(tasks: list[dict[str, Any]], model: Any, *, names_and_description: bool) -> list[tuple[dict[str, Any], list[tuple[str, float]]]]:
    texts: list[str] = []
    spans: list[tuple[int, int, dict[str, Any]]] = []
    for task in tasks:
        start = len(texts)
        texts.append(_old_text(task, names_and_description=names_and_description))
        texts.extend(_contract_text(contract, names_and_description=names_and_description) for contract in task["new_contracts"])
        spans.append((start, len(texts), task))
    vectors = model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False)
    results = []
    for start, end, task in spans:
        scores = [(contract["name"], float(vectors[start] @ vectors[start + index + 1])) for index, contract in enumerate(task["new_contracts"]) if start + index + 1 < end]
        results.append((_prediction_from_scores(task, scores), scores))
    return results


def predict_cross_encoder_batch(tasks: list[dict[str, Any]], model: Any) -> list[tuple[dict[str, Any], list[tuple[str, float]]]]:
    pairs: list[tuple[str, str]] = []
    spans: list[tuple[int, int, dict[str, Any]]] = []
    for task in tasks:
        start = len(pairs)
        old_text = _old_text(task, names_and_description=False)
        pairs.extend((old_text, _contract_text(contract, names_and_description=False)) for contract in task["new_contracts"])
        spans.append((start, len(pairs), task))
    values = model.predict(pairs, batch_size=32, show_progress_bar=False)
    results = []
    for start, end, task in spans:
        scores = [(contract["name"], float(values[start + index])) for index, contract in enumerate(task["new_contracts"]) if start + index < end]
        results.append((_prediction_from_scores(task, scores), scores))
    return results
