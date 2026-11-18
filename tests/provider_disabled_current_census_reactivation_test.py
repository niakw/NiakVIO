#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/reactivate_disabled_from_current_census.py"
spec = importlib.util.spec_from_file_location("current_census_reactivation", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, (dict, list)):
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    else:
        path.write_text(str(value), encoding="utf-8")


with tempfile.TemporaryDirectory(prefix="niakvio-disabled-current-census-") as tmp:
    root = Path(tmp)
    (root / "provider-disabled").mkdir()
    asset = root / "provider-disabled/demo.js"
    asset.write_text("module.exports={getStreams:async()=>[]};\n", encoding="utf-8")
    digest = hashlib.sha256(asset.read_bytes()).hexdigest()

    manifest = {"scrapers": [{
        "id": "demo",
        "enabled": False,
        "filename": "provider-disabled/demo.js",
        "supportedTypes": ["movie", "tv"],
        "disabledReason": "auto_off_current_architecture_nonfunctional",
        "disabledAt": "2026-11-14",
        "purgeAfter": "2026-11-21",
        "lifecycleState": "disabled-retained",
    }]}
    patch = {
        "manifest_overrides": {"enabled": False},
        "route_data_state": "off",
        "activation_eligible": False,
        "route_proof": {
            "authority": "observed-provider-http-request",
            "canonicalExecutionAuthority": {
                "coveredLanes": ["movie", "tv"],
                "missingLanes": [],
                "allEvidenceBackedAuthoritiesPreserved": True,
            },
        },
        "live_route_gate": {
            "completion_state": "declared-types-qualified",
            "validated_types": ["movie", "tv"],
        },
    }
    hubs = {"providers": {"demo": {
        "direct": "https://demo.example/",
        "manifest_status": "Désactivé",
        "activation_eligible": False,
    }}}
    overrides = {"provider_patches": {"demo": patch}}
    catalog = {"providers": []}

    write(root / "manifest.json", manifest)
    write(root / "provider_catalog.json", catalog)
    write(root / "provider-overrides.json", overrides)
    write(root / "provider-hubs.json", hubs)

    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "tested source"], cwd=root, check=True)
    trigger = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()

    run_id = "44221592944"
    status = {
        "runId": run_id,
        "triggerSha": trigger,
        "providers": [{
            "provider": "demo",
            "status": "DISABLED",
            "declaredLanes": ["movie", "tv"],
            "currentVerifiedLanes": ["movie", "tv"],
            "latestLaneVerdicts": ["movie=OK", "tv=OK"],
            "dominantIssue": "none",
            "brainCheckRequired": False,
            "testedThisRun": True,
        }],
    }
    summary = {
        "runId": run_id,
        "triggerSha": trigger,
        "verifiedProviders": ["demo"],
        "wrongContentProviders": [],
    }
    raw = {
        "schema_version": 6,
        "verified_providers": ["demo"],
        "wrong_content_providers": [],
        "rows": [
            {
                "provider_id": "demo", "semantic_type": "movie",
                "status": "playable_verified", "verified": 1,
                "contradictions": 0, "identity_safe": True,
                "fixture": {"tmdbId": "1", "mediaType": "movie", "title": "Movie"},
                "announced_quality_heights": [1080],
            },
            {
                "provider_id": "demo", "semantic_type": "tv",
                "status": "playable_verified", "verified": 1,
                "contradictions": 0, "identity_safe": True,
                "fixture": {
                    "tmdbId": "2", "mediaType": "tv", "title": "TV",
                    "season": 1, "episode": 1,
                },
                "announced_quality_heights": [1080],
            },
        ],
    }
    lifecycle = {"disabled": {"demo": {
        "state": "disabled-retained",
        "reason": "auto_off_current_architecture_nonfunctional",
        "disabledAt": "2026-11-14",
        "purgeAfter": "2026-11-21",
    }}}
    write(root / "automation/provider-census-status.json", status)
    write(root / f"automation/current-bytes-full-provider-census-{run_id}-summary.json", summary)
    write(root / f"automation/current-bytes-full-provider-census-{run_id}.json", raw)
    write(root / "automation/provider-disabled-lifecycle.json", lifecycle)

    proof = mod.validate_candidate(root, "demo")
    assert proof["proofAuthority"] == mod.PROOF_AUTHORITY
    assert proof["providerArtifactSha256"] == digest
    assert proof["declaredLanes"] == ["movie", "tv"]
    assert proof["verifiedLanes"] == ["movie", "tv"]
    assert proof["repairRequired"] is False
    assert proof["routeAuthorityVerified"] is True

    applied = mod.apply_proofs(root, [proof])
    assert applied["applied"] == ["demo"]
    updated_manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert updated_manifest["scrapers"][0]["enabled"] is True
    updated_overrides = json.loads((root / "provider-overrides.json").read_text(encoding="utf-8"))
    updated_patch = updated_overrides["provider_patches"]["demo"]
    assert "enabled" not in updated_patch.get("manifest_overrides", {})
    assert "route_data_state" not in updated_patch
    assert "activation_eligible" not in updated_patch
    assert updated_patch["disabled_reactivation_proof"]["providerArtifactSha256"] == digest
    ledger = json.loads(
        (root / "automation/provider-disabled-reactivation-ledger.json").read_text(encoding="utf-8")
    )
    assert ledger["providers"]["demo"]["proofAuthority"] == mod.PROOF_AUTHORITY

    # Restore disabled control-plane files for negative cases.
    write(root / "manifest.json", manifest)
    write(root / "provider-overrides.json", overrides)
    write(root / "provider-hubs.json", hubs)

    raw["rows"][1]["status"] = "wrong_content"
    write(root / f"automation/current-bytes-full-provider-census-{run_id}.json", raw)
    try:
        mod.validate_candidate(root, "demo")
    except mod.EligibilityError as exc:
        assert "contradiction" in str(exc) or "playable_verified" in str(exc)
    else:
        raise AssertionError("wrong-content lane was accepted")
    raw["rows"][1]["status"] = "playable_verified"
    write(root / f"automation/current-bytes-full-provider-census-{run_id}.json", raw)

    lifecycle["disabled"]["demo"]["reason"] = "manual_off_user_policy"
    write(root / "automation/provider-disabled-lifecycle.json", lifecycle)
    try:
        mod.validate_candidate(root, "demo")
    except mod.EligibilityError as exc:
        assert "not automatic architecture recovery debt" in str(exc)
    else:
        raise AssertionError("manual disable was automatically reactivated")
    lifecycle["disabled"]["demo"]["reason"] = "auto_off_current_architecture_nonfunctional"
    write(root / "automation/provider-disabled-lifecycle.json", lifecycle)

    asset.write_text("module.exports={getStreams:async()=>['drift']};\n", encoding="utf-8")
    try:
        mod.validate_candidate(root, "demo")
    except mod.EligibilityError as exc:
        assert "bytes drifted" in str(exc)
    else:
        raise AssertionError("provider byte drift was accepted")

    # A newer sharded-only status must not be mistaken for a published full
    # current-byte census, nor silently inherit the previous run's proof.
    (root / f"automation/current-bytes-full-provider-census-{run_id}-summary.json").unlink()
    try:
        mod.census_inputs(root)
    except mod.CensusEvidenceNotPublished as exc:
        assert run_id in str(exc)
        assert "no published full evidence" in str(exc)
    else:
        raise AssertionError("unpublished sharded status was accepted as full census proof")

print("current census exact-byte disabled reactivation contract passed")
