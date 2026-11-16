#!/usr/bin/env python3
"""Protect Global+France static-knowledge audit scope without magic counts."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import current_provider_scope as scope  # noqa: E402

audit = (ROOT / "scripts" / "audit_provider_v3_static.py").read_text(encoding="utf-8")
assert "projection_runtime_visible_provider_ids" in audit
assert "projection_active_provider_rows()" in audit
assert "active_provider_ids" not in audit
assert 'manifest.get("scrapers")' not in audit
assert "runtime_visible_provider_count" not in audit

global_runtime = scope.runtime_visible_provider_ids()
projection_runtime = scope.projection_runtime_visible_provider_ids()
assert global_runtime <= projection_runtime
assert len(projection_runtime) >= len(global_runtime)

print(
    "PROVIDER_STATIC_AUDIT_PROJECTION_SCOPE_OK "
    f"global_runtime={len(global_runtime)} projection_runtime={len(projection_runtime)} "
    f"france_only_runtime={len(projection_runtime-global_runtime)}"
)
