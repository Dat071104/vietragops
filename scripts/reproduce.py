"""Entrypoint alias for the Gate 19 reproducibility audit."""

from __future__ import annotations

import sys
from pathlib import Path

# Run reproduce_audit
from reproduce_audit import main

if __name__ == "__main__":
    sys.exit(main())
