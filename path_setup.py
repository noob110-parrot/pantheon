"""Ensure project root is on sys.path for `python main.py` and `python ui/...` runs."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
