"""Export benchmark and failure-analysis markdown from experiment JSON."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export benchmark markdown reports.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--benchmark-output", default="reports/benchmark_report.md")
    parser.add_argument("--failure-output", default="reports/failure_analysis.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    experiments = payload["experiments"]
    best = max(experiments, key=lambda item: (item["metrics"]["token_f1"], item["metrics"]["refusal_accuracy"]))

    benchmark_lines = [
        "# Benchmark Report",
        "",
        f"- Source experiment: `{args.input}`",
        f"- Experiment count: {len(experiments)}",
        "",
        "## Best config",
        "",
        f"- Config: `{best['config']}`",
        f"- Token F1: `{best['metrics']['token_f1']}`",
        f"- Refusal accuracy: `{best['metrics']['refusal_accuracy']}`",
    ]
    Path(args.benchmark_output).write_text("\n".join(benchmark_lines) + "\n", encoding="utf-8")

    worst = sorted(experiments, key=lambda item: item["metrics"]["unsupported_answer_rate"], reverse=True)[:5]
    label_counter = Counter()
    for item in experiments:
        for record in item.get("records", []):
            if record.get("failure_label"):
                label_counter[record["failure_label"]] += 1
    failure_lines = [
        "# Failure Analysis",
        "",
        f"- Source experiment: `{args.input}`",
        "",
        "## Failure label counts",
        "",
    ]
    for label, count in label_counter.most_common():
        failure_lines.append(f"- `{label}`: {count}")
    failure_lines.extend(
        [
            "",
        "## Highest unsupported-answer configs",
        "",
        ]
    )
    for item in worst:
        failure_lines.append(f"- `{item['config']}` -> unsupported answer rate `{item['metrics']['unsupported_answer_rate']}`")
    Path(args.failure_output).write_text("\n".join(failure_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
