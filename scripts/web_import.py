"""Local-only admin CLI for bounded Firecrawl web discovery/import.

There is no FastAPI route for this: the application has no admin
authorization mechanism to gate a public HTTP endpoint, so this
command-line tool -- run directly by an operator on this machine -- is the
only interface (Gate 03).

Usage:
    python scripts/web_import.py search --query "..." [--limit N]
    python scripts/web_import.py import --url "https://..." [--title "..."]
    python scripts/web_import.py recrawl --url "https://..." [--title "..."]

Output is a short status summary (document/version id, status) only --
never raw scraped Markdown, never the Firecrawl API key. Every imported
page is a candidate; nothing here reviews or publishes it.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from app.core.config import get_web_import_service


_REPO_ROOT = Path(__file__).resolve().parents[1]


def _should_load_dotenv() -> bool:
    return os.environ.get("PYTHON_DOTENV_DISABLED", "").strip().casefold() not in {"1", "true", "yes", "on"}


def _load_env_files() -> None:
    """Load the app's non-secret .env and the Gate-03 secret handoff file.

    Neither file's content is read, printed, or logged by this process --
    `load_dotenv` only sets process environment variables. The secret file
    is loaded with `override=False` so an operator's real shell export
    always wins over the file.
    """

    if not _should_load_dotenv():
        return
    load_dotenv(dotenv_path=_REPO_ROOT / ".env")
    firecrawl_env = _REPO_ROOT / ".env.firecrawl.local"
    if firecrawl_env.is_file():
        load_dotenv(dotenv_path=firecrawl_env, override=False)


def _cmd_search(args: argparse.Namespace) -> int:
    service = get_web_import_service()
    outcome = service.search_preview(args.query, limit=args.limit)
    if outcome.status != "ok":
        print(f"search failed: status={outcome.status} error_code={outcome.error_code}")
        return 1
    for descriptor in outcome.descriptors:
        print(f"- {descriptor.title!r} {descriptor.url}")
        if descriptor.description:
            print(f"  {descriptor.description}")
    print(f"({len(outcome.descriptors)} result(s))")
    return 0


def _cmd_import(args: argparse.Namespace) -> int:
    service = get_web_import_service()
    outcome = service.import_url(args.url, title=args.title)
    print(
        f"status={outcome.status} document_id={outcome.document_id} "
        f"version_id={outcome.version_id} parse_status={outcome.parse_status} "
        f"review_status={outcome.review_status} is_new_version={outcome.is_new_version}"
    )
    if outcome.status not in {"ok", "no_change"}:
        if outcome.error_code:
            print(f"error_code={outcome.error_code}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Admin-only bounded Firecrawl web import (local CLI, Gate 03).")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser(
        "search", help="Bounded search preview: title/url/description descriptors only, never scrapes."
    )
    search_parser.add_argument("--query", required=True)
    search_parser.add_argument("--limit", type=int, default=None)
    search_parser.set_defaults(func=_cmd_search)

    import_parser = subparsers.add_parser(
        "import", help="Validate, scrape one URL, and store the result as a review-only candidate."
    )
    import_parser.add_argument("--url", required=True)
    import_parser.add_argument("--title", default=None)
    import_parser.set_defaults(func=_cmd_import)

    recrawl_parser = subparsers.add_parser(
        "recrawl",
        help="Re-run import on an already-imported URL. Idempotent if unchanged; "
        "creates a new linked candidate version if the content changed.",
    )
    recrawl_parser.add_argument("--url", required=True)
    recrawl_parser.add_argument("--title", default=None)
    recrawl_parser.set_defaults(func=_cmd_import)

    return parser


def main(argv: list[str] | None = None) -> int:
    _load_env_files()
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
