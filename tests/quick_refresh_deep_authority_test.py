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
        "providers": [{"id": "historic", "enabled": True, "action": "quick-current-strict"}],
    }
    report_path.write_text(json.dumps(quick_generated), encoding="utf-8")

    original_provenance = {
        "providers": {
            "quarantined": {
                "published_filename": "providers/quarantined--nuvio-audit-quarantine--abc.js",
                "patched_sha256": "old-safe-sha",
                "activation_blockers": ["catalogue_audit_playable_identity_contradiction"],
            },
            "recovered": {
                "published_filename": "providers/recovered-old.js",
                "activation_eligible": False,
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
            "recovered": {
                "published_filename": "providers/recovered-new.js",
                "activation_eligible": True,
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
            {"recovered"},
        )
    finally:
        module.pc.REPORT_PATH = old_report_path
        module.pc.PROVENANCE_PATH = old_provenance_path
        module.REFRESH_REPORT_PATH = old_refresh_path

    # Deep report remains byte-for-byte canonical authority.
    assert report_path.read_bytes() == canonical_bytes

    refresh = json.loads(refresh_path.read_text(encoding="utf-8"))
    assert refresh["test_mode"] == "quick"
    assert refresh["publication_mode"] == "strict_existing_provider_refresh"
    assert refresh["policy"]["quick_refresh_may_recover_existing_provider"] is True
    assert refresh["policy"]["quick_refresh_blocks_brand_new_activation"] is True
    assert refresh["recovered_existing_provider_ids"] == ["recovered"]
    assert refresh["providers"][0]["action"] == "quick-current-strict"

    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    assert provenance["validation_mode"] == "quick"
    assert provenance["publication_mode"] == "strict_existing_provider_refresh"
    # Still-live quarantine keeps exact immutable provenance.
    assert provenance["providers"]["quarantined"] == original_provenance["providers"]["quarantined"]
    # Recovered provider keeps current quick-proof provenance; it must not be
    # restored to its old disabled/quarantine evidence.
    assert provenance["providers"]["recovered"]["published_filename"] == "providers/recovered-new.js"
    assert provenance["providers"]["recovered"]["activation_eligible"] is True
    assert provenance["providers"]["recovered"]["check_mode"] == "quick"
    assert provenance["providers"]["healthy"]["published_filename"] == "providers/healthy-new.js"
    assert provenance["providers"]["healthy"]["check_mode"] == "quick"

print("quick refresh deep authority test passed")
