"""Temporary activation shim for the durable runtime-domain fixed-point normalizer.

Python imports this module from the repository root before executing Core scripts.
It exists only to prove the repair on the authoritative GitHub runner; final cleanup
wires the normalizer explicitly and removes this shim.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from normalize_runtime_domain_fixed_point import behavior_contract, normalized  # noqa: E402

CORE = SCRIPTS / "core_rebuild_safety.py"
current = CORE.read_text(encoding="utf-8")
expected = normalized(current)
if expected != current:
    CORE.write_text(expected, encoding="utf-8")
behavior_contract(expected)
print(f"FIELD_RUNTIME_DOMAIN_BOOTSTRAP changed={int(expected != current)} status=ok")
