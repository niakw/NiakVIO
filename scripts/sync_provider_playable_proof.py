#!/usr/bin/env python3
"""Persist positive exact-bundle playable certification into provider repair authority.

This synchronizer is deliberately positive-only:
- a current bundle/lane playable_verified witness may add durable proof;
- a complete exact-bundle certificate may promote route_data_state to on;
- Node/CI negatives never erase prior, locked or Native evidence and never disable.

The exact bundle SHA is recorded so later rematerialization can distinguish current
proof from historical/workbench proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "manifest.json"
DEFAULT_OVERRIDES = ROOT / "provider-overrides.json"
DEFAULT_CERTIFICATION = ROOT / "automation/provider-playable-certification.json"
DEFAULT_REPORT = ROOT / "automation/provider-playable-proof-sync.json"
LANES = {"movie", "tv", "anime"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path}: JSON object required")
    return value


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def semantic_types(row: dict[str, Any]) -> set[str]:
    values = row.get("canonicalSupportedTypes")
    if not isinstance(values, list) or not values:
        values = row.get("supportedTypes") or []
    return {cid(value) for value in values if cid(value) in LANES}


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def default_sha_lookup(row: dict[str, Any]) -> str | None:
    filename = str(row.get("filename") or "").strip()
    return sha256_file((ROOT / filename).resolve()) if filename else None


def certification_rows(certification: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        cid(row.get("providerId")): row
        for row in certification.get("providers") or []
        if isinstance(row, dict) and cid(row.get("providerId"))
    }


def positive_lanes(
    manifest_row: dict[str, Any],
    cert_row: dict[str, Any],
    *,
    current_sha: str | None,
) -> tuple[set[str], bool, str]:
    if not current_sha:
        return set(), False, "bundle_missing"
    if str(cert_row.get("bundleSha256") or "") != current_sha:
        return set(), False, "bundle_sha_mismatch"
    required = semantic_types(manifest_row)
    cert_required = {cid(value) for value in cert_row.get("requiredTypes") or [] if cid(value) in LANES}
    if required != cert_required:
        return set(), False, "certificate_lane_scope_mismatch"
    lanes = cert_row.get("lanes") if isinstance(cert_row.get("lanes"), dict) else {}
    certified_types = {cid(value) for value in cert_row.get("certifiedTypes") or [] if cid(value) in LANES}
    positive = {
        lane
        for lane in required
        if lane in certified_types
        and isinstance(lanes.get(lane), dict)
        and lanes[lane].get("state") == "certified"
    }
    complete = bool(required) and positive == required and bool(cert_row.get("certified"))
    return positive, complete, "exact_bundle_positive" if positive else "no_positive_lane"


def sync(
    manifest: dict[str, Any],
    overrides: dict[str, Any],
    certification: dict[str, Any],
    *,
    sha_lookup: Callable[[dict[str, Any]], str | None] = default_sha_lookup,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if certification.get("authority") != "exact-bundle-playable-lane-certification-v1":
        raise RuntimeError("exact-bundle playable certification authority required")

    manifest_rows = {
        cid(row.get("id")): row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and cid(row.get("id"))
    }
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    patches = dict(patches)
    certs = certification_rows(certification)
    changed: list[str] = []
    complete: list[str] = []
    partial: list[str] = []
    ignored: dict[str, str] = {}

    for provider, cert_row in sorted(certs.items()):
        manifest_row = manifest_rows.get(provider)
        patch = patches.get(provider)
        if not isinstance(manifest_row, dict) or not isinstance(patch, dict):
            ignored[provider] = "manifest_or_override_missing"
            continue

        current_sha = sha_lookup(manifest_row)
        positive, exact_complete, reason = positive_lanes(manifest_row, cert_row, current_sha=current_sha)
        if not positive:
            ignored[provider] = reason
            continue

        required = semantic_types(manifest_row)
        disposition = dict(patch.get("repair_disposition") or {})
        old_current = {cid(value) for value in disposition.get("currentVerifiedLanes") or [] if cid(value) in LANES}
        old_proven = {cid(value) for value in disposition.get("provenLanes") or [] if cid(value) in LANES}
        current = old_current | positive
        proven = old_proven | positive

        lane_statuses = disposition.get("laneStatuses") if isinstance(disposition.get("laneStatuses"), dict) else {}
        lane_statuses = {
            cid(lane): list(values) if isinstance(values, list) else []
            for lane, values in lane_statuses.items()
            if cid(lane) in LANES
        }
        for lane in sorted(positive):
            statuses = [str(value) for value in lane_statuses.get(lane, []) if str(value)]
            if "playable_verified" not in statuses:
                statuses.append("playable_verified")
            lane_statuses[lane] = sorted(set(statuses))

        previous_missing = {cid(value) for value in disposition.get("missingLanes") or [] if cid(value) in LANES}
        if exact_complete:
            current = set(required)
            proven = set(required)
            missing: set[str] = set()
        else:
            missing = previous_missing - positive
            if not previous_missing:
                missing = set(required) - positive

        proof_lanes: dict[str, Any] = {}
        cert_lanes = cert_row.get("lanes") if isinstance(cert_row.get("lanes"), dict) else {}
        for lane in sorted(positive):
            lane_row = cert_lanes.get(lane) if isinstance(cert_lanes.get(lane), dict) else {}
            proof_lanes[lane] = {
                "state": "certified",
                "fixtureSlug": lane_row.get("fixtureSlug"),
            }

        exact_proof = {
            "authority": "exact-bundle-playable-lane-certification-v1",
            "manifestVersion": certification.get("manifestVersion"),
            "generatedAt": certification.get("generatedAt"),
            "filename": manifest_row.get("filename"),
            "bundleSha256": current_sha,
            "verifiedLanes": sorted(positive),
            "complete": exact_complete,
            "lanes": proof_lanes,
        }

        disposition.update({
            "schemaVersion": 1,
            "authority": "provider-repair-disposition-v1",
            "requiredLanes": sorted(required),
            "currentVerifiedLanes": sorted(current),
            "provenLanes": sorted(proven),
            "missingLanes": sorted(missing),
            "laneStatuses": lane_statuses,
            "evidenceDestructive": False,
            "exactBundleProof": exact_proof,
        })
        reasons = [str(value) for value in disposition.get("reasonCodes") or [] if str(value)]
        reasons = [value for value in reasons if value != "exact_bundle_playable_certification_v1"]
        reasons.append("exact_bundle_playable_certification_v1")

        if exact_complete:
            disposition["completeCapabilityProof"] = True
            disposition["recoveryStatus"] = "proven"
            disposition["routeDataState"] = "on"
            reasons = [
                value for value in reasons
                if value not in {
                    "declared_lane_unproven",
                    "repair_survival_restored_requires_exact_bundle_reproof",
                    "fresh_identity_safe_positive_required",
                }
            ]
            if "all_declared_lanes_live_proven" not in reasons:
                reasons.append("all_declared_lanes_live_proven")
            patch["route_data_state"] = "on"
            current_stream_proof = dict(patch.get("current_stream_proof") or {})
            current_stream_proof.update({
                "authority": "exact-bundle-playable-lane-certification-v1",
                "streamPositive": True,
                "requiresFreshIdentitySafePositive": False,
                "bundleSha256": current_sha,
                "filename": manifest_row.get("filename"),
                "manifestVersion": certification.get("manifestVersion"),
                "verifiedLanes": sorted(required),
                "verifiedAt": certification.get("generatedAt"),
            })
            patch["current_stream_proof"] = current_stream_proof
            complete.append(provider)
        else:
            disposition["completeCapabilityProof"] = bool(disposition.get("completeCapabilityProof"))
            partial.append(provider)

        disposition["reasonCodes"] = sorted(set(reasons))
        patch["repair_disposition"] = disposition
        patches[provider] = patch
        changed.append(provider)

    output = dict(overrides)
    output["provider_patches"] = patches
    report = {
        "schemaVersion": 1,
        "authority": "provider-playable-proof-sync-v1",
        "sourceAuthority": certification.get("authority"),
        "manifestVersion": certification.get("manifestVersion"),
        "fullManifestCensus": bool(certification.get("fullManifestCensus")),
        "changedProviders": changed,
        "changedProviderCount": len(changed),
        "completeExactBundleProviders": complete,
        "completeExactBundleProviderCount": len(complete),
        "partialPositiveProviders": partial,
        "ignoredProviders": ignored,
        "negativeEvidenceDestructive": False,
    }
    return output, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--overrides", type=Path, default=DEFAULT_OVERRIDES)
    parser.add_argument("--certification", type=Path, default=DEFAULT_CERTIFICATION)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    manifest = load(args.manifest.resolve())
    overrides = load(args.overrides.resolve())
    certification = load(args.certification.resolve())
    output, report = sync(manifest, overrides, certification)
    if args.check:
        if output != overrides:
            print(
                "FIELD_PROVIDER_PLAYABLE_PROOF_SYNC "
                f"status=drift changed={report['changedProviderCount']} "
                f"complete={report['completeExactBundleProviderCount']}"
            )
            return 1
        print("FIELD_PROVIDER_PLAYABLE_PROOF_SYNC status=fixed-point")
        return 0

    dump(args.overrides.resolve(), output)
    dump(args.report.resolve(), report)
    print(
        "FIELD_PROVIDER_PLAYABLE_PROOF_SYNC "
        f"changed={report['changedProviderCount']} "
        f"complete={report['completeExactBundleProviderCount']} "
        f"partial={len(report['partialPositiveProviders'])} "
        "negative_destructive=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
