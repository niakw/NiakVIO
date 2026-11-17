#!/usr/bin/env python3
"""Proof-bound reactivation for lifecycle-disabled providers.

A disabled provider may be reactivated without a code mutation only when an
isolated Disabled Provider Recovery Lab has proven the *same bytes* playable
with identity evidence on every declared lane and the Brain explicitly abstained
from repair.  This transaction changes activation/control-plane state only, then
hands relocation/projections to the existing lifecycle implementation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
CATALOG = ROOT / "provider_catalog.json"
OVERRIDES = ROOT / "provider-overrides.json"
LEDGER = ROOT / "automation/provider-disabled-reactivation-ledger.json"

def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")

def load(path: Path, default: Any = None) -> Any:
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))

def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def provider_source_row(root: Path, provider: str) -> tuple[str, dict[str, Any], dict[str, Any]]:
    manifest_path = root / "manifest.json"
    manifest = load(manifest_path)
    for row in manifest.get("scrapers") or []:
        if isinstance(row, dict) and canon(row.get("id")) == provider:
            return "global", row, manifest

    catalog_path = root / "provider_catalog.json"
    catalog = load(catalog_path)
    for entry in catalog.get("providers") or []:
        if not isinstance(entry, dict):
            continue
        scraper = entry.get("scraper") if isinstance(entry.get("scraper"), dict) else {}
        projections = entry.get("projections") if isinstance(entry.get("projections"), dict) else {}
        pid = canon(entry.get("canonicalId") or scraper.get("id"))
        if pid != provider:
            continue
        if projections.get("general") is False and projections.get("vf") is True:
            return "france", scraper, catalog
        raise RuntimeError(f"{provider}: catalogue identity is not Global or France-only")
    raise RuntimeError(f"{provider}: provider not found in current catalogue")

def artifact_path(root: Path, filename: object) -> Path:
    rel = str(filename or "").strip().replace("\\", "/")
    while rel.startswith("../"):
        rel = rel[3:]
    path = (root / rel).resolve()
    if root.resolve() not in path.parents:
        raise RuntimeError("provider artifact escapes repository")
    return path

def find_stage_candidate(stage: dict[str, Any], provider: str) -> dict[str, Any]:
    rows = [
        row for row in stage.get("candidates") or []
        if isinstance(row, dict) and canon(row.get("canonical_id") or row.get("upstream_id")) == provider
    ]
    if len(rows) != 1:
        raise RuntimeError(f"{provider}: expected one disabled recovery stage candidate, got {len(rows)}")
    return rows[0]

def find_health(health: dict[str, Any], provider: str) -> dict[str, Any]:
    rows = [
        row for row in health.get("results") or []
        if isinstance(row, dict) and canon(row.get("canonical_id") or row.get("upstream_id")) == provider
    ]
    if len(rows) != 1:
        raise RuntimeError(f"{provider}: expected one health row, got {len(rows)}")
    return rows[0]

def identity_verified_lanes(row: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    proven: dict[str, list[dict[str, Any]]] = {}
    for test in row.get("tests") or []:
        if not isinstance(test, dict):
            continue
        fixture = test.get("fixture") if isinstance(test.get("fixture"), dict) else {}
        lane = canon(fixture.get("category") or fixture.get("mediaType"))
        if not lane:
            continue
        hosts = []
        for host in test.get("host_results") or []:
            if not isinstance(host, dict):
                continue
            if (
                host.get("playback_verified") is True
                and host.get("payload_verified") is True
                and str(host.get("content_identity_status") or "") == "match"
                and host.get("duration_identity_mismatch") is not True
            ):
                hosts.append({
                    "host": host.get("host"),
                    "kind": host.get("kind"),
                    "reason": host.get("content_identity_reason"),
                })
        if hosts:
            proven.setdefault(lane, []).append({
                "fixture": fixture.get("label") or fixture.get("title") or fixture.get("tmdbId"),
                "tmdbId": str(fixture.get("tmdbId") or ""),
                "hosts": hosts,
            })
    return proven


def validate_recovery(
    root: Path,
    provider: str,
    artifact_root: Path,
    *,
    proof_run_id: str,
    proof_head_sha: str,
) -> dict[str, Any]:
    provider = canon(provider)
    scope, source_row, _ = provider_source_row(root, provider)
    if source_row.get("enabled") is not False:
        raise RuntimeError(f"{provider}: provider is not disabled")
    if str(source_row.get("lifecycleState") or "") != "disabled-retained":
        raise RuntimeError(f"{provider}: provider is not lifecycle-disabled")
    filename = str(source_row.get("filename") or "")
    if "provider-disabled/" not in filename.replace("\\", "/"):
        raise RuntimeError(f"{provider}: disabled artifact is not under provider-disabled/")

    current_asset = artifact_path(root, filename)
    if not current_asset.is_file():
        raise RuntimeError(f"{provider}: disabled artifact missing: {current_asset}")
    current_sha = sha256(current_asset)

    stage = load(artifact_root / "staging-disabled-recovery/candidates.json")
    candidate = find_stage_candidate(stage, provider)
    if candidate.get("disabled_recovery_exact_bytes") is not True:
        raise RuntimeError(f"{provider}: recovery did not stage exact disabled bytes")
    if candidate.get("production_execution_allowed") is not False or candidate.get("publication_allowed") is not False:
        raise RuntimeError(f"{provider}: recovery stage unexpectedly had publication authority")
    stage_sha = str(candidate.get("sha256") or "").strip().casefold()
    if current_sha != stage_sha:
        raise RuntimeError(f"{provider}: current disabled bytes drifted from recovery proof")

    health = load(artifact_root / "brain-disabled-recovery/health/health-results.json")
    row = find_health(health, provider)
    if str(row.get("sha256") or "").strip().casefold() != current_sha:
        raise RuntimeError(f"{provider}: health proof SHA does not match current disabled bytes")
    if str(row.get("status") or "") != "healthy":
        raise RuntimeError(f"{provider}: recovery health is not healthy")
    if str(row.get("ci_classification") or "") != "conclusive_success":
        raise RuntimeError(f"{provider}: recovery health is not conclusive")

    profile = row.get("candidate_profile") if isinstance(row.get("candidate_profile"), dict) else {}
    evidence = row.get("evidence") if isinstance(row.get("evidence"), dict) else {}
    declared = {canon(v) for v in (profile.get("required_fixture_categories") or source_row.get("canonicalSupportedTypes") or source_row.get("supportedTypes") or []) if canon(v)}
    healthy = {canon(v) for v in evidence.get("healthy_fixture_categories") or [] if canon(v)}
    if not declared or not declared.issubset(healthy):
        raise RuntimeError(f"{provider}: not every declared lane has healthy recovery evidence")
    if int(evidence.get("streams_playable") or 0) < len(declared):
        raise RuntimeError(f"{provider}: insufficient playable streams for declared lanes")
    if int(evidence.get("payload_verified_streams") or 0) < len(declared):
        raise RuntimeError(f"{provider}: insufficient payload-verified streams")
    if int(evidence.get("identity_verified_streams") or 0) < len(declared):
        raise RuntimeError(f"{provider}: insufficient identity-verified streams")
    lane_identity = identity_verified_lanes(row)
    missing_identity_lanes = sorted(declared - set(lane_identity))
    if missing_identity_lanes:
        raise RuntimeError(
            f"{provider}: missing per-lane identity-verified playable proof for {missing_identity_lanes}"
        )
    for key in (
        "identity_contradiction_count",
        "duration_identity_mismatch_count",
        "playable_identity_contradiction_count",
        "playable_duration_identity_mismatch_count",
        "streams_rejected_identity",
        "streams_rejected_duration",
    ):
        if int(evidence.get(key) or 0) != 0:
            raise RuntimeError(f"{provider}: recovery evidence contains {key}")
    if evidence.get("provider_server_accessible") is not True or evidence.get("provider_server_successful_response") is not True:
        raise RuntimeError(f"{provider}: provider server was not successfully reached")

    disposition = load(artifact_root / "brain-disabled-recovery/brain-llm/recovery-disposition.json")
    if canon(disposition.get("provider")) != provider:
        raise RuntimeError(f"{provider}: recovery disposition provider mismatch")
    required_disposition = {
        "brainAbstained": True,
        "currentDisabledHealthHealthy": True,
        "residentialTransportActive": True,
        "repairRequired": False,
        "publicationAuthority": False,
        "directMutationAuthority": False,
    }
    for key, expected in required_disposition.items():
        if disposition.get(key) is not expected:
            raise RuntimeError(f"{provider}: invalid recovery disposition {key}={disposition.get(key)!r}")
    if str(disposition.get("nextAction") or "") != "exact_playback_identity_replay":
        raise RuntimeError(f"{provider}: Brain did not request exact playback identity replay")
    if int(disposition.get("brainGuidanceRows") or 0) != 0:
        raise RuntimeError(f"{provider}: Brain emitted mutation guidance despite healthy bytes")

    guidance = load(artifact_root / "brain-disabled-recovery/brain-llm/guidance.json")
    if int(guidance.get("providerCount") or 0) != 0 or list(guidance.get("rows") or []):
        raise RuntimeError(f"{provider}: recovery guidance contains provider mutations")
    if guidance.get("directMutationAuthority") is not False or guidance.get("publicationAuthority") is not False:
        raise RuntimeError(f"{provider}: guidance unexpectedly has mutation/publication authority")
    if str(guidance.get("sourceSha") or "") != proof_head_sha:
        raise RuntimeError(f"{provider}: guidance source SHA does not match recovery run")

    return {
        "provider": provider,
        "scope": scope,
        "providerArtifactSha256": current_sha,
        "proofRunId": str(proof_run_id),
        "proofHeadSha": str(proof_head_sha),
        "proofStatus": "terminal_identity_verified",
        "brainAbstained": True,
        "repairRequired": False,
        "directMutationAuthority": False,
        "declaredLanes": sorted(declared),
        "verifiedLanes": sorted(set(lane_identity) & declared),
        "laneIdentityEvidence": lane_identity,
        "streamsPlayable": int(evidence.get("streams_playable") or 0),
        "payloadVerifiedStreams": int(evidence.get("payload_verified_streams") or 0),
        "identityVerifiedStreams": int(evidence.get("identity_verified_streams") or 0),
        "verifiedMaxHeight": int(row.get("verified_max_height") or evidence.get("verified_max_height") or 0),
        "audioLanguages": sorted({str(v) for v in row.get("audio_languages") or evidence.get("audio_languages") or [] if str(v)}),
        "proofAuthority": "disabled-recovery-exact-byte-residential-v1",
    }

def apply_reactivation(root: Path, proof: dict[str, Any], *, today: str | None = None) -> dict[str, Any]:
    if root.resolve() != ROOT.resolve():
        raise RuntimeError("apply is supported only on the repository root")
    provider = canon(proof["provider"])
    scope, source_row, source_doc = provider_source_row(root, provider)
    if scope != proof["scope"]:
        raise RuntimeError(f"{provider}: scope drifted since recovery validation")

    source_row["enabled"] = True
    if scope == "global":
        dump(root / "manifest.json", source_doc)
    else:
        dump(root / "provider_catalog.json", source_doc)

    overrides_path = root / "provider-overrides.json"
    overrides = load(overrides_path)
    patches = overrides.setdefault("provider_patches", {})
    patch = patches.setdefault(provider, {})
    # Lifecycle/folder state is the activation authority. Reactivation records
    # its exact-byte proof but must not leave a second enabled=true override
    # that can outlive a later lifecycle decision.
    manifest_overrides = patch.get("manifest_overrides") if isinstance(patch.get("manifest_overrides"), dict) else {}
    manifest_overrides.pop("enabled", None)
    if manifest_overrides:
        patch["manifest_overrides"] = manifest_overrides
    else:
        patch.pop("manifest_overrides", None)
    patch["disabled_reactivation_proof"] = dict(proof)
    dump(overrides_path, overrides)

    # Existing lifecycle owns file relocation, derived projections, catalog,
    # disabled-state cleanup, static knowledge and materialization reconciliation.
    import sys
    scripts_dir = root / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import manage_provider_lifecycle as lifecycle
    day = lifecycle.parse_day(today) if today else lifecycle.today_utc()
    report = lifecycle.apply_lifecycle(day=day, apply=True)
    if provider not in set(report.get("reenabled") or []):
        raise RuntimeError(f"{provider}: lifecycle did not record reactivation")

    _, active_row, _ = provider_source_row(root, provider)
    if active_row.get("enabled") is False:
        raise RuntimeError(f"{provider}: provider remained disabled after lifecycle")
    active_path = artifact_path(root, active_row.get("filename"))
    if "providers/" not in str(active_row.get("filename") or "").replace("\\", "/") or "provider-disabled/" in str(active_row.get("filename") or ""):
        raise RuntimeError(f"{provider}: lifecycle did not move provider to active directory")
    if sha256(active_path) != proof["providerArtifactSha256"]:
        raise RuntimeError(f"{provider}: provider bytes changed during reactivation")

    ledger = load(LEDGER, {"schemaVersion": 1, "authority": "provider-disabled-reactivation-ledger-v1", "providers": {}})
    ledger["schemaVersion"] = 1
    ledger["authority"] = "provider-disabled-reactivation-ledger-v1"
    providers = ledger.setdefault("providers", {})
    providers[provider] = dict(proof, reactivatedAt=day.isoformat())
    dump(LEDGER, ledger)
    return {"proof": proof, "lifecycle": report, "activeFilename": active_row.get("filename")}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", required=True)
    ap.add_argument("--artifact-root", type=Path, required=True)
    ap.add_argument("--proof-run-id", required=True)
    ap.add_argument("--proof-head-sha", required=True)
    ap.add_argument("--today")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--receipt", type=Path)
    args = ap.parse_args()

    proof = validate_recovery(
        ROOT, canon(args.provider), args.artifact_root,
        proof_run_id=args.proof_run_id,
        proof_head_sha=args.proof_head_sha,
    )
    result: dict[str, Any] = {"validated": True, "proof": proof}
    if args.apply:
        result["transaction"] = apply_reactivation(ROOT, proof, today=args.today)
    if args.receipt:
        dump(args.receipt, result)
    print(
        "FIELD_DISABLED_REACTIVATION",
        f"provider={proof['provider']}",
        f"scope={proof['scope']}",
        f"lanes={','.join(proof['verifiedLanes'])}",
        f"identity_verified={proof['identityVerifiedStreams']}",
        f"apply={str(args.apply).lower()}",
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
