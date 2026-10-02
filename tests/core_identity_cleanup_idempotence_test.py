#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "apply_core_identity_ownership_cleanup.py"
IDENTITY = ROOT / "scripts" / "provider_patches" / "global_stream_identity_v1.py"

spec = importlib.util.spec_from_file_location("identity_cleanup_idempotence", SCRIPT)
assert spec and spec.loader
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)

identity = IDENTITY.read_text(encoding="utf-8")
assert "cross-client-player-page-identity-v15" in identity
assert cleanup.identity_semantics_current(identity)
cleanup.validate_source_state()

# Running the migration entrypoint against a newer Core revision that already
# satisfies the behavior contract must be a no-op success, not a v10-anchor
# failure that blocks the entire provider Repair pipeline.
assert cleanup.main() == 0

print("Core identity cleanup idempotence contract passed")
