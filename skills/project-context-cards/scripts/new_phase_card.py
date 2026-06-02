#!/usr/bin/env python3
import argparse
from pathlib import Path
from datetime import date

TEMPLATE = """# Phase Context Card: {title}\n\n## Phase goal\n\nTBD.\n\n## Inputs needed\n\n- Project context\n- Implementation log\n- Previous phase outputs\n\n## Expected outputs\n\n- TBD\n\n## Files/folders owned by this phase\n\n- TBD\n\n## Commands/scripts\n\n```bash\n# add commands here\n```\n\n## Quality gate\n\n- TBD\n\n## Do not do\n\n- Do not fake metrics.\n- Do not skip implementation log.\n- Do not read unrelated code without zone-brain.\n\n## Current status\n\nnot_started\n\n## Open questions\n\n- TBD\n\n## Next handoff\n\nCreated: {today}\n"""

def main():
    p = argparse.ArgumentParser(description='Create a phase context card.')
    p.add_argument('--phase', required=True)
    p.add_argument('--title', required=True)
    p.add_argument('--out', required=True)
    args = p.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise SystemExit(f'refusing to overwrite existing file: {out}')
    out.write_text(TEMPLATE.format(title=args.title, today=date.today().isoformat()), encoding='utf-8')
    print(f'created {out}')

if __name__ == '__main__':
    main()
