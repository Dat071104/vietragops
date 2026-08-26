# Tools

Copies of the workspace-pack scripts, so this project can run them without the
pack being installed. Do not hand-edit: re-running `init_project_ops.py`
overwrites this folder. Fix the pack instead.

Run every tool from the project root:

```bash
python _agent_ops/tools/session_start.py --root .
python _agent_ops/tools/explore.py --symbol <name>
```
