#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import materialize_provider_v3_one as one
from reconcile_targeted_provider_publication import data_digest, reconcile

with tempfile.TemporaryDirectory() as tmp_name:
    root = Path(tmp_name)
    (root / "providers").mkdir(parents=True)
    data = {
        "providerId": "vidlove",
        "apiRecipe": {
            "base": "https://api.vidlove.cc",
            "directRoute": "/{media}?id={tmdbId}&sources=moviebox",
        },
    }
    payload = base64.b64encode(
        json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
    body = (
        "/* STARTFIX:PROVIDER.VIDLOVE.CONFIG.V1 */ "
        f"/* FIXDATA:PROVIDER.VIDLOVE.CONFIG.V1:{payload} */ "
        "const NIAKVIO_PROVIDER_MODEL = Object.freeze({}); "
        "/* CLOSEFIX:PROVIDER.VIDLOVE.CONFIG.V1 */"
    )
    current_rel = "providers/vidlove-workspace.js"
    current_path = root / current_rel
    current_path.write_text(body, encoding="utf-8")
    raw = current_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()

    (root / "manifest.json").write_text(json.dumps({
        "scrapers": [{"id": "vidlove", "filename": current_rel}]
    }), encoding="utf-8")
    (root / "provider-v3-materialization.json").write_text(json.dumps({
        "providers": [{
            "provider": "vidlove",
            "file": "providers/vidlove--nuvio--old000000000000.js",
            "sha256": "0" * 64,
            "providerDataSha256": "0" * 64,
        }]
    }), encoding="utf-8")

    (root / "PROVENANCE.json").write_text(json.dumps({
        "providers": {
            "vidlove": {
                "published_filename": "providers/vidlove--nuvio--old000000000000.js",
                "sha256": "0" * 64,
                "patched_sha256": "0" * 64,
                "final_fixed_point": {"sha256": "0" * 64},
                "final_minimizer": {"sha256": "0" * 64, "saved_bytes": 7, "transformed_lines": 3},
            }
        }
    }), encoding="utf-8")

    sync_calls = []
    def sync_stub(*, check: bool):
        assert check is False
        sync_calls.append(check)

    updates = reconcile(root, ["vidlove"], sync_projections=sync_stub)
    assert sync_calls == [False], sync_calls
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    material = json.loads((root / "provider-v3-materialization.json").read_text(encoding="utf-8"))
    provenance = json.loads((root / "PROVENANCE.json").read_text(encoding="utf-8"))
    mrow = manifest["scrapers"][0]
    prow = material["providers"][0]
    vrow = provenance["providers"]["vidlove"]

    assert mrow["filename"] == prow["file"]
    assert mrow["filename"].startswith("providers/vidlove--nuvio--")
    assert mrow["filename"].endswith(f"{digest[:16]}.js")
    assert (root / mrow["filename"]).read_bytes() == raw
    assert prow["sha256"] == digest
    assert prow["providerDataSha256"] == data_digest(data)
    assert vrow["published_filename"] == mrow["filename"]
    assert vrow["sha256"] == digest
    assert vrow["patched_sha256"] == digest
    assert vrow["final_fixed_point"]["sha256"] == digest
    assert vrow["final_minimizer"]["sha256"] == digest
    assert vrow["final_minimizer"]["saved_bytes"] == 7
    assert vrow["final_minimizer"]["transformed_lines"] == 3
    assert material["providerCount"] == 1
    assert material["activeProviderIdentityCount"] == 1
    assert material["expectedProviderCount"] == 1
    assert material["targetedPublicationComplete"] is True
    assert material["targetedPublicationFixedPointProviders"] == ["vidlove"]
    assert updates[0]["to"] == mrow["filename"]


# Targeted materialization must upsert its exact row even when the historical
# ledger is partial, remove inactive rows, and never claim completeness until
# every active identity has a ledger row.
with tempfile.TemporaryDirectory() as tmp_name:
    root = Path(tmp_name)
    report_path = root / "provider-v3-materialization.json"
    report_path.write_text(json.dumps({
        "schemaVersion": 3,
        "providers": [
            {"provider": "alpha", "file": "providers/alpha.js", "sha256": "1" * 64},
            {"provider": "fr-only", "file": "providers/fr-only.js", "sha256": "5" * 64},
            {"provider": "inactive", "file": "providers/inactive.js", "sha256": "2" * 64},
        ],
        "providerCount": 2,
        "expectedProviderCount": 2,
    }), encoding="utf-8")

    old_report = one.allmat.DEFAULT_REPORT
    old_active = one.projection_active_provider_ids
    try:
        one.allmat.DEFAULT_REPORT = report_path
        one.projection_active_provider_ids = lambda: {"alpha", "movy", "chillflix", "fr-only"}
        ledger = one.upsert_materialization_report({
            "provider": "movy",
            "file": "providers/movy-new.js",
            "sha256": "3" * 64,
            "providerDataSha256": "4" * 64,
        })
    finally:
        one.allmat.DEFAULT_REPORT = old_report
        one.projection_active_provider_ids = old_active

    rows = {row["provider"]: row for row in ledger["providers"]}
    assert set(rows) == {"alpha", "fr-only", "movy"}, rows
    assert rows["movy"]["file"] == "providers/movy-new.js"
    assert rows["fr-only"]["file"] == "providers/fr-only.js", "France-only active row retained"
    assert ledger["providerCount"] == 3
    assert ledger["activeProviderIdentityCount"] == 4
    assert ledger["expectedProviderCount"] == 4
    assert ledger["targetedMaterializedProviders"] == ["movy"]
    persisted = json.loads(report_path.read_text(encoding="utf-8"))
    assert persisted["providerCount"] == 3
    assert persisted["expectedProviderCount"] == 4

print("targeted ledger upsert passed: exact provider row persisted, stale inactive row dropped, incomplete active scope remains explicit")

print("targeted provider publication reconcile passed: manifest/materialization/public bytes converge after final targeted materialization")
