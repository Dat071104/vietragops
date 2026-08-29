"""Write the Gate 08 protocol so it can be committed before any headline run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from research.gate08.protocol.freeze import build_protocol, write_protocol


DEFAULT_MODELS = "openai/gpt-oss-120b,openai/gpt-oss-20b"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--models", default=DEFAULT_MODELS)
    parser.add_argument("--cost-cap-usd", type=float, default=1.20)
    parser.add_argument("--created-at", required=True)
    args = parser.parse_args()

    protocol = build_protocol(
        model_ids=tuple(value.strip() for value in args.models.split(",") if value.strip()),
        cost_cap_usd=args.cost_cap_usd,
        created_at=args.created_at,
    )
    target = write_protocol(protocol, args.output)
    print(
        json.dumps(
            {
                "output": str(target).replace("\\", "/"),
                "git_head_at_freeze": protocol["git_head_at_freeze"],
                "method_interface_digest": protocol["method"]["interface_digest"],
                "eval_case_count": protocol["evaluation_surface"]["eval_case_count"],
                "calibration_case_count": protocol["evaluation_surface"]["calibration_case_count"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
