"""Load the one-shot Core repair from the repository root, then remove this shim."""
from __future__ import annotations

from pathlib import Path

SELF = Path(__file__).resolve()
try:
    import scripts.sitecustomize  # noqa: F401
finally:
    if SELF.exists():
        SELF.unlink()
