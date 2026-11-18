#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/disable_active_wrong_content_from_current_census.py"
spec = importlib.util.spec_from_file_location("wrong_content_lifecycle", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, (dict, list)):
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    else:
        path.write_text(str(value), encoding="utf-8")


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True)
    return result.stdout.strip()


with tempfile.TemporaryDirectory(prefix="niakvio-wrong-content-lifecycle-") as tmp:
    root = Path(tmp)
    (root / "providers").mkdir()
    (root / "automation").mkdir()
    git(root, "init")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "NiakVIO Test")

    provider_bytes = b"module.exports={getStreams:async()=>[]};\n"
    provider_path = root / "providers/demo--nuvio--1111111111111111.js"
    provider_path.write_bytes(provider_bytes)
    manifest = {"scrapers": [{
        "id": "DEMO", "enabled": True, "supportedTypes": ["movie", "tv"],
        "filename": "providers/demo--nuvio--1111111111111111.js",
    }]}
    catalog = {"providers": [{
        "canonicalId": "demo", "scraper": dict(manifest["scrapers"][0]),
        "projections": {"general": True, "vf": False},
    }]}
    overrides = {"provider_patches": {"demo": {
        "capability": "html_scraper", "manifest_overrides": {},
    }}}
    hubs = {"providers": {"demo": {
        "id": "demo", "manifest_status": "Active", "direct": "https://demo.example",
    }}}
    write(root / "manifest.json", manifest)
    write(root / "provider_catalog.json", catalog)
    write(root / "provider-overrides.json", overrides)
    write(root / "provider-hubs.json", hubs)
    git(root, "add", ".")
    git(root, "commit", "-m", "baseline")
    trigger_sha = git(root, "rev-parse", "HEAD")

    run_id = "123456"
    status = {
        "runId": run_id, "triggerSha": trigger_sha,
        "providers": [{
            "provider": "demo", "status": "PROVIDER JS BROKEN",
            "declaredLanes": ["movie", "tv"], "currentVerifiedLanes": [],
            "latestLaneVerdicts": [
                "movie=playable_unverified/provider_returned_streams",
                "tv=wrong_content/provider_returned_wrong_content",
            ],
            "dominantIssue": "provider_returned_streams, provider_returned_wrong_content",
            "testedThisRun": True, "brainCheckRequired": True,
            "repairEligible": False,
        }],
    }
    summary = {
        "runId": int(run_id), "triggerSha": trigger_sha,
        "wrongContentProviders": ["demo"],
    }
    raw = {
        "schema_version": 6,
        "rows": [{
            "provider_id": "demo", "semantic_type": "tv",
            "status": "wrong_content", "contradictions": 1,
            "identity_safe": False,
        }],
    }
    write(root / "automation/provider-census-status.json", status)
    write(root / f"automation/current-bytes-full-provider-census-{run_id}-summary.json", summary)
    write(root / f"automation/current-bytes-full-provider-census-{run_id}.json", raw)

    proof = mod.validate_candidate(root, "demo")
    assert proof["proofAuthority"] == mod.PROOF_AUTHORITY
    assert proof["wrongContent"] is True
    assert proof["contradictoryLanes"] == ["tv"]
    assert proof["directProviderMutationAuthority"] is False

    provider_path.write_bytes(provider_bytes + b"// newer\n")
    try:
        mod.validate_candidate(root, "demo")
    except mod.EligibilityError as exc:
        assert "active bytes changed" in str(exc)
    else:
        raise AssertionError("stale negative census was allowed to disable newer bytes")
    provider_path.write_bytes(provider_bytes)

    current_hubs = json.loads((root / "provider-hubs.json").read_text(encoding="utf-8"))
    current_hubs["providers"]["demo"]["direct"] = "https://new.demo.example"
    write(root / "provider-hubs.json", current_hubs)
    try:
        mod.validate_candidate(root, "demo")
    except mod.EligibilityError as exc:
        assert "hub/domain authority changed" in str(exc)
    else:
        raise AssertionError("stale wrong-content evidence survived authority drift")
    write(root / "provider-hubs.json", hubs)

    current_summary = dict(summary)
    current_summary["wrongContentProviders"] = []
    write(root / f"automation/current-bytes-full-provider-census-{run_id}-summary.json", current_summary)
    try:
        mod.validate_candidate(root, "demo")
    except mod.EligibilityError as exc:
        assert "not in current-run wrong-content set" in str(exc)
    else:
        raise AssertionError("provider absent from wrong-content set was disabled")
    write(root / f"automation/current-bytes-full-provider-census-{run_id}-summary.json", summary)

    result = mod.apply_proofs(root, [proof])
    assert result["applied"] == ["demo"]
    updated_manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert updated_manifest["scrapers"][0]["enabled"] is False
    assert updated_manifest["scrapers"][0]["disabledReason"] == mod.DISABLE_REASON
    updated_overrides = json.loads((root / "provider-overrides.json").read_text(encoding="utf-8"))
    patch = updated_overrides["provider_patches"]["demo"]
    assert patch["manifest_overrides"]["enabled"] is False
    assert patch["activation_eligible"] is False
    assert patch["wrong_content_disable_proof"]["providerArtifactSha256"] == proof["providerArtifactSha256"]
    assert "manual_off_reason" not in patch
    updated_hubs = json.loads((root / "provider-hubs.json").read_text(encoding="utf-8"))
    assert updated_hubs["providers"]["demo"]["manifest_status"] == "Désactivé"
    assert updated_hubs["providers"]["demo"]["activation_eligible"] is False

    # Sharded status can be fresher than the persisted full census. Unattended
    # lifecycle must defer without touching provider, manifest or patch bytes.
    (root / f"automation/current-bytes-full-provider-census-{run_id}-summary.json").unlink()
    original_root, original_latest, original_argv = mod.ROOT, mod.LATEST, sys.argv
    receipt_path = root / "automation/provider-active-wrong-content-disable-latest.json"
    try:
        mod.ROOT = root
        mod.LATEST = receipt_path
        sys.argv = [str(SCRIPT), "--apply"]
        manifest_before = (root / "manifest.json").read_bytes()
        provider_before = provider_path.read_bytes()
        assert mod.main() == 0
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        assert receipt["deferred"] is True
        assert receipt["deferredReason"] == "full-current-byte-census-not-published"
        assert receipt["sourceCensusRunId"] == run_id
        assert receipt["eligible"] == [] and receipt["applied"] == []
        assert (root / "manifest.json").read_bytes() == manifest_before
        assert provider_path.read_bytes() == provider_before
        sys.argv = [str(SCRIPT), "--apply", "--provider", "demo"]
        assert mod.main() == 2
    finally:
        mod.ROOT, mod.LATEST, sys.argv = original_root, original_latest, original_argv

print("active exact-byte wrong-content lifecycle contract passed")
