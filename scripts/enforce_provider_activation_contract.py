#!/usr/bin/env python3
"""Enforce NiakVIO's published active-provider contract.

A provider may remain enabled only when the exact currently referenced bundle has a
fresh all-declared-lanes playable certificate. Uncertified providers are retained
in the visible disabled/repair lifecycle; they are never silently deleted.

Re-enabling is intentionally explicit: ``--allow-reenable`` is valid only for a
fresh exact-bundle certificate and is meant for Repair/Learning promotion flows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "manifest.json"
DEFAULT_CERTIFICATION = ROOT / "automation/provider-playable-certification.json"
DEFAULT_MINIMUM_BULK_YIELD = 0.75
MIN_BULK_PROVIDER_COUNT = 8
LANES = {"movie", "tv", "anime"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path}: JSON object required")
    return value


def dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def semantic_types(row: dict[str, Any]) -> set[str]:
    values = row.get("canonicalSupportedTypes")
    if not isinstance(values, list) or not values:
        values = row.get("supportedTypes") or []
    return {cid(value) for value in values if cid(value) in LANES}


def file_sha(row: dict[str, Any]) -> str | None:
    filename = str(row.get("filename") or "").strip()
    if not filename:
        return None
    path = (ROOT / filename).resolve()
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def certification_by_id(certification: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        cid(row.get("providerId")): row
        for row in certification.get("providers") or []
        if isinstance(row, dict) and cid(row.get("providerId"))
    }


def exact_certified(row: dict[str, Any], cert: dict[str, Any] | None) -> tuple[bool, str]:
    if not isinstance(cert, dict):
        return False, "missing_certificate"
    current_sha = file_sha(row)
    if not current_sha:
        return False, "bundle_missing"
    if str(cert.get("bundleSha256") or "") != current_sha:
        return False, "bundle_sha_mismatch"
    manifest_required = semantic_types(row)
    cert_required = {cid(value) for value in cert.get("requiredTypes") or [] if cid(value) in LANES}
    certified = {cid(value) for value in cert.get("certifiedTypes") or [] if cid(value) in LANES}
    if not manifest_required:
        return False, "no_declared_semantic_lane"
    if cert_required != manifest_required:
        return False, "certificate_lane_scope_mismatch"
    missing = manifest_required - certified
    if not bool(cert.get("certified")) or missing:
        return False, "missing_playable_lane:" + ",".join(sorted(missing))
    return True, "exact_bundle_all_lanes_playable"


def enforce(
    manifest: dict[str, Any],
    certification: dict[str, Any],
    *,
    allow_reenable: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if certification.get("authority") != "exact-bundle-playable-lane-certification-v1":
        raise RuntimeError("exact-bundle playable certification authority required")
    certs = certification_by_id(certification)
    changed = False
    disabled: list[str] = []
    reenabled: list[str] = []
    kept: list[str] = []
    decisions: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for original in manifest.get("scrapers") or []:
        if not isinstance(original, dict):
            continue
        row = dict(original)
        provider = cid(row.get("id"))
        was_enabled = row.get("enabled") is not False
        ok, reason = exact_certified(row, certs.get(provider))
        if ok:
            if was_enabled:
                kept.append(provider)
            elif allow_reenable and str(row.get("disabledReason") or "").startswith("uncertified_playable_output"):
                row["enabled"] = True
                row.pop("disabledReason", None)
                row.pop("activationState", None)
                reenabled.append(provider)
                changed = True
        elif was_enabled:
            row["enabled"] = False
            row["disabledReason"] = f"uncertified_playable_output:{reason}"
            row["activationState"] = "repair-learning-required"
            disabled.append(provider)
            changed = True
        decisions.append({
            "providerId": provider,
            "wasEnabled": was_enabled,
            "exactCertified": ok,
            "reason": reason,
            "action": "disabled" if provider in disabled else "reenabled" if provider in reenabled else "kept",
        })
        rows.append(row)
    output = {**manifest, "scrapers": rows}
    manifest_rows = [row for row in (manifest.get("scrapers") or []) if isinstance(row, dict) and cid(row.get("id"))]
    manifest_total = len(manifest_rows)
    active_before = [cid(row.get("id")) for row in manifest_rows if row.get("enabled") is not False]
    certified_before = [row["providerId"] for row in decisions if row["wasEnabled"] and row["exactCertified"]]
    certified_manifest = [row["providerId"] for row in decisions if row["exactCertified"]]
    full_manifest_census = (
        bool(certification.get("fullManifestCensus"))
        and int(certification.get("manifestProviderCount") or 0) == manifest_total
        and int(certification.get("selectedProviderCount") or certification.get("providerCount") or 0) == manifest_total
    )
    yield_ratio = (len(certified_manifest) / manifest_total) if full_manifest_census and manifest_total else None
    active_yield_ratio = (len(certified_before) / len(active_before)) if active_before else 1.0
    report = {
        "schemaVersion": 1,
        "authority": "provider-activation-contract-v1",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "manifestVersion": manifest.get("version"),
        "changed": changed,
        "fullManifestCensus": full_manifest_census,
        "manifestProviderCount": manifest_total,
        "exactCertifiedManifest": certified_manifest,
        "exactCertifiedManifestCount": len(certified_manifest),
        "activeBefore": active_before,
        "activeBeforeCount": len(active_before),
        "exactCertifiedBefore": certified_before,
        "exactCertifiedBeforeCount": len(certified_before),
        "bootstrapYieldRatio": round(yield_ratio, 4) if yield_ratio is not None else None,
        "activeYieldRatio": round(active_yield_ratio, 4),
        "keptActive": kept,
        "disabledNow": disabled,
        "reenabledNow": reenabled,
        "activeAfter": [cid(row.get("id")) for row in rows if row.get("enabled") is not False],
        "disabledAfter": [cid(row.get("id")) for row in rows if row.get("enabled") is False],
        "decisions": decisions,
    }
    return output, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--certification", type=Path, default=DEFAULT_CERTIFICATION)
    parser.add_argument("--report", type=Path, default=ROOT / "automation/provider-activation-contract.json")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--allow-reenable", action="store_true")
    parser.add_argument("--apply-lifecycle", action="store_true")
    parser.add_argument("--minimum-bulk-yield", type=float, default=DEFAULT_MINIMUM_BULK_YIELD)
    parser.add_argument("--require-yield", action="store_true", help="exit non-zero when a significant batch is below the architecture yield floor")
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    certification = load(args.certification.resolve())
    manifest = load(manifest_path)
    output, report = enforce(manifest, certification, allow_reenable=args.allow_reenable)
    minimum_yield = max(0.0, min(float(args.minimum_bulk_yield), 1.0))
    significant_batch = int(report["manifestProviderCount"]) >= MIN_BULK_PROVIDER_COUNT
    full_manifest_census = bool(report["fullManifestCensus"])
    global_ratio = report.get("bootstrapYieldRatio")
    architecture_ok = (
        full_manifest_census
        and ((not significant_batch) or (global_ratio is not None and float(global_ratio) >= minimum_yield))
    )
    report["minimumBulkYield"] = minimum_yield
    report["significantBatch"] = significant_batch
    report["architectureState"] = (
        "auto-yield-sufficient"
        if architecture_ok
        else "architecture-defect-low-auto-yield"
        if full_manifest_census
        else "targeted-diagnostic-no-global-yield"
    )
    report["massDisableBlocked"] = bool((not architecture_ok) and report["disabledNow"])
    args.report.resolve().parent.mkdir(parents=True, exist_ok=True)
    dump(args.report.resolve(), report)
    print(
        "FIELD_PROVIDER_ACTIVATION_CONTRACT "
        f"active_after={len(report['activeAfter'])} disabled_now={len(report['disabledNow'])} "
        f"reenabled_now={len(report['reenabledNow'])} changed={str(report['changed']).lower()} apply={str(args.apply).lower()}"
    )
    if report["fullManifestCensus"]:
        print(
            "FIELD_PROVIDER_ACTIVATION_YIELD "
            f"certified_manifest={report['exactCertifiedManifestCount']}/{report['manifestProviderCount']} "
            f"certified_active={report['exactCertifiedBeforeCount']}/{report['activeBeforeCount']} "
            f"ratio={report['bootstrapYieldRatio']:.4f} floor={minimum_yield:.4f} "
            f"architecture={report['architectureState']} mass_disable_blocked={str(report['massDisableBlocked']).lower()}"
        )
    else:
        print(
            "FIELD_PROVIDER_ACTIVATION_YIELD "
            f"certified_manifest=unknown/{report['manifestProviderCount']} "
            f"selected_evidence_exact={report['exactCertifiedManifestCount']} "
            f"global_ratio=unknown floor={minimum_yield:.4f} "
            f"architecture={report['architectureState']} mass_disable_blocked=true"
        )
    for row in report["decisions"]:
        if not row["exactCertified"]:
            print(
                "FIELD_PROVIDER_ACTIVATION_UNCERTIFIED "
                f"provider={row['providerId']} reason={row['reason']} action={row['action']}"
            )
    if (args.apply or args.require_yield) and not full_manifest_census:
        print("FIELD_PROVIDER_ACTIVATION_REFUSED reason=full_manifest_census_required")
        return 3
    if (args.apply or args.require_yield) and not architecture_ok:
        print("FIELD_PROVIDER_ACTIVATION_REFUSED reason=architecture_yield_below_floor")
        return 3
    if args.apply:
        dump(manifest_path, output)
        if args.apply_lifecycle:
            if manifest_path != DEFAULT_MANIFEST.resolve():
                raise RuntimeError("lifecycle apply requires repository manifest.json")
            subprocess.run(
                [sys.executable, str(ROOT / "scripts/manage_provider_lifecycle.py"), "--apply"],
                cwd=ROOT,
                check=True,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
