"""Delegate the temporary Core bootstrap to its single durable owner.

This root shim exists only so GitHub runner Python startup reaches the one-shot
materializer in ``scripts/sitecustomize.py``.  It must never patch Core itself:
having two bootstrap owners previously caused the root shim to overwrite the
more complete historical-orphan cleaner with an exact-payload-only variant.
The inner bootstrap materializes the fail-closed Core/test changes and removes
itself plus the temporary workflow; this shim then removes itself as well.
"""
from __future__ import annotations

from pathlib import Path

SELF = Path(__file__).resolve()

try:
    import scripts.sitecustomize  # noqa: F401
finally:
    if SELF.exists():
        SELF.unlink()
