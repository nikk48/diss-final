"""Backward-compatible wrapper for the Part B import command."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.import_partb_results import main


if __name__ == "__main__":
    main()
