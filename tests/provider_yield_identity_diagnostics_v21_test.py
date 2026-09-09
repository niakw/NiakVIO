#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_provider_repair_yield_v6.py"

spec = importlib.util.spec_from_file_location("yield_diag", SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit("unable to load targeted yield audit")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

probe = {
    "streams": [
        {
            "row": {"url": "https://secret.invalid/master.m3u8?token=SECRET", "title": "Sensitive title"},
            "identity": {"status": "contradiction", "reason": "wrong_episode", "url": "https://secret.invalid/"},
            "metadata_identity": {"status": "match", "reason": "expected_title_alias", "raw": "Sensitive title"},
            "duration_identity": {"status": "contradiction", "reason": "fixture_duration_mismatch", "duration_ratio": 2.345678, "token": "SECRET"},
        }
    ] * 12
}
rows = module.safe_identity_diagnostics(probe)
assert len(rows) == 8, rows
assert rows[0]["identity"] == {"status": "contradiction", "reason": "wrong_episode"}, rows[0]
assert rows[0]["metadata_identity"] == {"status": "match", "reason": "expected_title_alias"}, rows[0]
assert rows[0]["duration_identity"] == {
    "status": "contradiction",
    "reason": "fixture_duration_mismatch",
    "duration_ratio": 2.3457,
}, rows[0]
serialized = repr(rows)
for forbidden in ("secret.invalid", "SECRET", "Sensitive title", "master.m3u8", "token"):
    assert forbidden not in serialized, serialized

print("provider yield identity diagnostics V21 safety tests passed")
