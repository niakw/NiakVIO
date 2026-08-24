"""Temporary Python-start shim for the durable runtime-domain fixed-point normalizer.

The authoritative Core run publishes the resulting durable source. This shim is
removed during final cleanup once the exact resulting main proves the fixed point.
"""
from __future__ import annotations

from pathlib import Path

try:
    from normalize_runtime_domain_fixed_point import behavior_contract, normalized

    root = Path(__file__).resolve().parents[1]
    core = root / "scripts" / "core_rebuild_safety.py"
    current = core.read_text(encoding="utf-8")
    expected = normalized(current)
    if expected != current:
        core.write_text(expected, encoding="utf-8")
    behavior_contract(expected)
    print(f"FIELD_RUNTIME_DOMAIN_BOOTSTRAP changed={int(expected != current)} status=ok")
except Exception as exc:
    print(f"FIELD_RUNTIME_DOMAIN_BOOTSTRAP status=error type={type(exc).__name__} detail={exc}")
    raise
