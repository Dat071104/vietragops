#!/usr/bin/env python3
import argparse
from datetime import datetime
from pathlib import Path

TEMPLATE = """## {timestamp} - [{phase}/{type}] {title}\n\n### Goal\n- {goal}\n\n### Files changed\n{files}\n\n### Bug or issue fixed\n- Symptom: {symptom}\n- Root cause: {root_cause}\n- Fix: {fix}\n- Why this fix is safe: {safety}\n\n### Commands run\n```bash\n{commands}\n```\n\n### Verification\n- {verification}\n\n### Decisions\n- {decisions}\n\n### Remaining risks / next step\n- {risks}\n\n"""

def bulletize(value: str) -> str:
    items = [x.strip() for x in value.split(',') if x.strip()]
    return '\n'.join(f'- `{x}`' for x in items) if items else '- none'

def main():
    p = argparse.ArgumentParser(description='Append a structured implementation log entry.')
    p.add_argument('--log', default='IMPLEMENTATION_LOG.md')
    p.add_argument('--title', required=True)
    p.add_argument('--phase', default='unknown_phase')
    p.add_argument('--type', default='implementation')
    p.add_argument('--goal', default='not specified')
    p.add_argument('--files', default='')
    p.add_argument('--symptom', default='not applicable')
    p.add_argument('--root-cause', default='not applicable')
    p.add_argument('--fix', default='not applicable')
    p.add_argument('--safety', default='not specified')
    p.add_argument('--commands', default='not run')
    p.add_argument('--verification', default='not verified')
    p.add_argument('--decisions', default='none')
    p.add_argument('--risks', default='none')
    args = p.parse_args()

    log_path = Path(args.log)
    existing = log_path.read_text(encoding='utf-8') if log_path.exists() else '# Implementation Log\n\n<!-- newest first -->\n'
    entry = TEMPLATE.format(
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M'),
        phase=args.phase,
        type=args.type,
        title=args.title,
        goal=args.goal,
        files=bulletize(args.files),
        symptom=args.symptom,
        root_cause=args.root_cause,
        fix=args.fix,
        safety=args.safety,
        commands=args.commands,
        verification=args.verification,
        decisions=args.decisions,
        risks=args.risks,
    )
    marker = '<!-- newest first -->'
    if marker in existing:
        updated = existing.replace(marker, marker + '\n\n' + entry, 1)
    else:
        updated = existing.rstrip() + '\n\n' + entry
    log_path.write_text(updated, encoding='utf-8')
    print(f'appended log entry to {log_path}')

if __name__ == '__main__':
    main()
