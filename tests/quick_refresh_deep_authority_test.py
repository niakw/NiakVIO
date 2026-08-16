#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts" / "promote_refresh_candidates.py"
spec = importlib.util.spec_from_file_location("promote_refresh_candidates", path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory() as directory:
    tmp = Path(directory)
    report_path = tmp / "health-report.json"
    refresh_path = tmp / "refresh-health-report.json"
    provenance_path = tmp / "PROVENANCE.json"

    canonical = {
        "test_mode": "deep",
        "providers": [
            {
                "id": "historic",
                "enabled": False,
                "action": "published-disabled-failed-gates",
                "failed_gates": ["04_playable_stream"],
            }
        ],
    }
    canonical_bytes = (json.dumps(canonical, indent=2) + "\n").encode("utf-8")

    quick_generated = {
        "test_mode": "deep",
        "providers": [{"id": "historic", "enabled": False, "action": "quick-generated"}],
    }
    report_path.write_text(json.dumps(quick_generated), encoding="utf-8")

    original_provenance = {
        "providers": {
            "quarantined": {
                "published_filename": "providers/quarantined--nuvio-audit-quarantine--abc.js",
                "patched_sha256": "old-safe-sha",
                "activation_blockers": ["catalogue_audit_playable_identity_contradiction"],
            },
            "healthy": {"published_filename": "providers/healthy-old.js"},
        }
    }
    generated_provenance = {
        "providers": {
            "quarantined": {
                "published_filename": "providers/quarantined-live.js",
                "patched_sha256": "unsafe-new-sha",
                "checked_at": "now",
            },
            "healthy": {
                "published_filename": "providers/healthy-new.js",
                "checked_at": "now",
            },
        }
    }
    provenance_path.write_text(json.dumps(generated_provenance), encoding="utf-8")

    old_report_path = module.pc.REPORT_PATH
    old_provenance_path = module.pc.PROVENANCE_PATH
    old_refresh_path = module.REFRESH_REPORT_PATH
    try:
        module.pc.REPORT_PATH = report_path
        module.pc.PROVENANCE_PATH = provenance_path
        module.REFRESH_REPORT_PATH = refresh_path
        module._postprocess_refresh_outputs(
            canonical_bytes,
            original_provenance,
            {"quarantined"},
        )
    finally:
        module.pc.REPORT_PATH = old_report_path
        module.pc.PROVENANCE_PATH = old_provenance_path
        module.REFRESH_REPORT_PATH = old_refresh_path

    assert report_path.read_bytes() == canonical_bytes

    refresh = json.loads(refresh_path.read_text(encoding="utf-8"))
    assert refresh["test_mode"] == "quick"
    assert refresh["publication_mode"] == "restricted_quick_refresh"
    assert refresh["policy"]["quick_refresh_preserves_activation_set"] is True
    assert refresh["providers"][0]["action"] == "quick-generated"

    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    assert provenance["validation_mode"] == "quick"
    assert provenance["publication_mode"] == "restricted_quick_refresh"
    assert provenance["providers"]["quarantined"] == original_provenance["providers"]["quarantined"]
    assert provenance["providers"]["healthy"]["published_filename"] == "providers/healthy-new.js"
    assert provenance["providers"]["healthy"]["check_mode"] == "quick"

print("quick refresh deep authority test passed")
