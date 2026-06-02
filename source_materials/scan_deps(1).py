#!/usr/bin/env python3
"""
zone-brain / scan_deps.py
Build a Python dependency graph and return the "affected zone"
for a given task keyword or file seed.

Usage:
    python scan_deps.py --root ./my_project --seed "auth,user" --hops 2
    python scan_deps.py --root . --seed "payment" --hops 2 --output json
"""

import os
import ast
import json
import argparse
from pathlib import Path
from collections import defaultdict, deque


# ─── 1. SCAN ──────────────────────────────────────────────────────────────────

def collect_python_files(root: str) -> list[Path]:
    """Walk the project and collect all .py files, skipping junk dirs."""
    SKIP_DIRS = {
        ".git", "__pycache__", ".venv", "venv", "env", "node_modules",
        ".mypy_cache", ".pytest_cache", "dist", "build", ".tox", "migrations"
    }
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune skip dirs in-place
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            if f.endswith(".py"):
                files.append(Path(dirpath) / f)
    return files


# ─── 2. MAP (import extraction) ───────────────────────────────────────────────

def extract_imports(filepath: Path) -> list[str]:
    """
    Parse a .py file with AST and return all imported module names.
    Falls back to grep-style line scan if AST fails (syntax errors, etc).
    """
    try:
        source = filepath.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source, filename=str(filepath))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split(".")[0])
        return list(set(imports))
    except Exception:
        # Fallback: simple line scan
        lines = []
        try:
            for line in filepath.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if line.startswith("import ") or line.startswith("from "):
                    parts = line.split()
                    if len(parts) >= 2:
                        lines.append(parts[1].split(".")[0])
        except Exception:
            pass
        return list(set(lines))


def build_graph(root: str, files: list[Path]) -> dict:
    """
    Build adjacency: { relative_path -> [list of local module paths it imports] }
    Only tracks intra-project imports (ignores stdlib / third-party).
    """
    root_path = Path(root).resolve()

    # Map module name → relative file path
    module_map: dict[str, str] = {}
    for f in files:
        rel = f.resolve().relative_to(root_path)
        parts = list(rel.parts)
        # e.g. src/auth/utils.py → "utils", "auth.utils", "src.auth.utils"
        for i in range(len(parts)):
            key = ".".join(parts[i:]).removesuffix(".py")
            module_map[key] = str(rel)

    graph: dict[str, list[str]] = defaultdict(list)
    for f in files:
        rel = str(f.resolve().relative_to(root_path))
        imports = extract_imports(f)
        for imp in imports:
            if imp in module_map:
                target = module_map[imp]
                if target != rel:
                    graph[rel].append(target)

    return dict(graph)


# ─── 3. ZONE (BFS from seed files) ────────────────────────────────────────────

def find_seed_files(keywords: list[str], files: list[Path], root: str) -> list[str]:
    """
    Find files whose path or name contains any of the keywords.
    Returns relative paths.
    """
    root_path = Path(root).resolve()
    seeds = []
    kws = [k.lower().strip() for k in keywords]
    for f in files:
        rel = str(f.resolve().relative_to(root_path))
        if any(kw in rel.lower() for kw in kws):
            seeds.append(rel)
    return seeds


def build_reverse_graph(graph: dict) -> dict:
    """Who imports this file? (reverse edges for impact tracing)"""
    reverse: dict[str, list[str]] = defaultdict(list)
    for src, deps in graph.items():
        for dep in deps:
            reverse[dep].append(src)
    return dict(reverse)


def bfs_zone(seeds: list[str], graph: dict, reverse_graph: dict, hops: int) -> set[str]:
    """
    BFS outward from seed files in BOTH directions:
    - forward  (what does this file depend on?)
    - backward (who depends on this file? = impact zone)
    Returns a set of relative file paths in the affected zone.
    """
    visited = set(seeds)
    queue = deque([(s, 0) for s in seeds])

    while queue:
        node, depth = queue.popleft()
        if depth >= hops:
            continue
        neighbors = graph.get(node, []) + reverse_graph.get(node, [])
        for nb in neighbors:
            if nb not in visited:
                visited.add(nb)
                queue.append((nb, depth + 1))

    return visited


# ─── 4. OUTPUT ────────────────────────────────────────────────────────────────

def summarize_zone(zone: set[str], root: str, seeds: list[str], graph: dict) -> dict:
    """Build a clean summary dict for AI consumption."""
    root_path = Path(root).resolve()
    result = {
        "seed_files": seeds,
        "zone_files": sorted(zone),
        "zone_count": len(zone),
        "edges": {
            f: graph.get(f, [])
            for f in sorted(zone)
            if graph.get(f)
        },
        "read_order": _topological_sort(zone, graph),
    }
    return result


def _topological_sort(zone: set[str], graph: dict) -> list[str]:
    """Return files in dependency order (deps first) for sequential reading."""
    in_degree = {f: 0 for f in zone}
    for f in zone:
        for dep in graph.get(f, []):
            if dep in zone:
                in_degree[f] += 1  # f depends on dep → read dep first

    queue = deque([f for f, d in in_degree.items() if d == 0])
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for f in zone:
            if node in graph.get(f, []) and f in in_degree:
                in_degree[f] -= 1
                if in_degree[f] == 0:
                    queue.append(f)

    # Append any remaining (cycles)
    remaining = [f for f in zone if f not in order]
    return order + remaining


def print_context_prompt(summary: dict, root: str) -> str:
    """
    Generate the exact text you paste into Cursor / Codex as context.
    Only the zone files, in read order, with their content.
    """
    lines = ["# 🧠 ZONE-BRAIN CONTEXT\n"]
    lines.append(f"**Seed files** (matched your task): {summary['seed_files']}\n")
    lines.append(f"**Affected zone**: {summary['zone_count']} files\n")
    lines.append("---\n")

    root_path = Path(root).resolve()
    for rel in summary["read_order"]:
        filepath = root_path / rel
        lines.append(f"\n## 📄 `{rel}`\n```python")
        try:
            lines.append(filepath.read_text(encoding="utf-8", errors="ignore"))
        except Exception as e:
            lines.append(f"# Could not read: {e}")
        lines.append("```\n")

    return "\n".join(lines)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="zone-brain: Python dependency zone finder")
    parser.add_argument("--root", default=".", help="Project root directory")
    parser.add_argument("--seed", required=True, help="Comma-separated keywords or file names, e.g. 'auth,login'")
    parser.add_argument("--hops", type=int, default=2, help="BFS depth (default: 2)")
    parser.add_argument("--output", choices=["context", "json", "files"], default="context",
                        help="context = paste-ready prompt | json = raw graph | files = just file list")
    args = parser.parse_args()

    keywords = [k.strip() for k in args.seed.split(",")]

    print(f"🔍 Scanning {args.root} ...", flush=True)
    files = collect_python_files(args.root)
    print(f"   Found {len(files)} Python files")

    print("🗺️  Building dependency graph ...")
    graph = build_graph(args.root, files)

    print(f"🎯 Finding seeds for: {keywords}")
    seeds = find_seed_files(keywords, files, args.root)
    if not seeds:
        print("⚠️  No seed files found! Try broader keywords.")
        return

    print(f"   Seeds: {seeds}")

    reverse = build_reverse_graph(graph)
    zone = bfs_zone(seeds, graph, reverse, hops=args.hops)
    summary = summarize_zone(zone, args.root, seeds, graph)

    print(f"✅ Zone: {summary['zone_count']} files (from {len(files)} total, saved {len(files)-summary['zone_count']} unnecessary reads)\n")

    if args.output == "json":
        print(json.dumps(summary, indent=2))
    elif args.output == "files":
        for f in summary["read_order"]:
            print(f)
    else:  # context
        prompt = print_context_prompt(summary, args.root)
        out_path = Path(args.root) / ".zone_context.md"
        out_path.write_text(prompt, encoding="utf-8")
        print(f"📋 Context saved to: {out_path}")
        print("   → Paste .zone_context.md content into Cursor / Codex before your task.\n")
        print("─" * 60)
        print(prompt[:2000] + ("\n... (truncated, see file)" if len(prompt) > 2000 else ""))


if __name__ == "__main__":
    main()
