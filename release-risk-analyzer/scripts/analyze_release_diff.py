#!/usr/bin/env python3
"""Compatibility wrapper for review_release_risk.py."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> int:
    runpy.run_path(
        str(Path(__file__).with_name("review_release_risk.py")),
        run_name="__main__",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
