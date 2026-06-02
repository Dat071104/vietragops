#!/usr/bin/env python3
import argparse
from pathlib import Path

REQUIRED = [
    'README.md',
    'docker-compose.yml',
    'Dockerfile',
    '.env.example',
    'app/main.py',
    'evals/datasets/golden_qa.jsonl',
    'evals/experiments/compare_pipelines.py',
    'reports/benchmark_report.md',
    'reports/failure_analysis.md',
    'tests',
    '.github/workflows/ci.yml',
]


def main():
    p = argparse.ArgumentParser(description='Check required VietRAGOps release files.')
    p.add_argument('--root', default='.')
    args = p.parse_args()
    root = Path(args.root)
    missing = []
    present = []
    for rel in REQUIRED:
        path = root / rel
        if path.exists():
            present.append(rel)
        else:
            missing.append(rel)
    print('present:')
    for x in present:
        print(f'  ok  {x}')
    print('missing:')
    for x in missing:
        print(f'  miss {x}')
    if missing:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
