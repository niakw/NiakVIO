#!/usr/bin/env python3
"""Record route-proof diagnostics without mutating catalogue activation.

Route proof owns route/DATA confidence, not publication exposure. A provider with no
currently proven route may be diagnostic ``off`` and must still remain present in the
catalogue. Route proof must not write, remove, or reinterpret any ``enabled`` field in
the manifest or provider overrides. Runtime repair remains fail-closed when no usable
route exists; activation is owned exclusively by the catalogue/final publication policy.

The health report still records the no-proven-route gate so Repair/Learn can retain the
debt and evidence without turning that evidence into a destructive catalogue change.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "automation" / "provider-route-recovery-v5.json"
DEFAULT_MANIFEST = ROOT / "manifest.json"
DEFAULT_OVERRIDES = ROOT / "provider-overrides.json"
DEFAULT_HEALTH_REPORT = ROOT / "health-report.json"
ROUTE_PROOF_DIAGNOSTIC_ACTION = "route-proof-no-proven-route-diagnostic"
LEGACY_ROUTE_PROOF_DISABLE_ACTION = "published-disabled-no-proven-route"
ROUTE_PROOF_FAILED_GATE = "route_proof_no_proven_route"
ROUTE_PROOF_AUTHORITY = "provider-route-recovery-v5"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path}: expected object")
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def health_row(health: dict[str, Any], provider_id: str) -> dict[str, Any]:
    providers = health.get("providers")
    if not isinstance(providers, list):
        providers = []
        health["providers"] = providers
    for row in providers:
        if isinstance(row, dict) and cid(row.get("id")) == provider_id:
            return row
    row: dict[str, Any] = {"id": provider_id}
    providers.append(row)
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--overrides", type=Path, default=DEFAULT_OVERRIDES)
    parser.add_argument("--health-report", type=Path, default=DEFAULT_HEALTH_REPORT)
    args = parser.parse_args()

    report = load(args.report)
    manifest = load(args.manifest)
    overrides = load(args.overrides)
    health = load(args.health_report) if args.health_report.is_file() else {"providers": []}
    rows = report.get("providers") if isinstance(report.get("providers"), list) else []
    recovered = {
        cid(row.get("providerId")): row
        for row in rows
        if isinstance(row, dict) and cid(row.get("providerId"))
    }
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}

    movix_proof = recovered.get("movix")
    movix_patch = patches.get("movix") if isinstance(patches.get("movix"), dict) else None
    if not isinstance(movix_proof, dict) or not isinstance(movix_patch, dict):
        raise SystemExit("MOVIX route proof/DATA missing")

    proven_routes = [str(value) for value in movix_proof.get("routes") or [] if str(value).strip()]
    route_proof = movix_patch.get("route_proof") if isinstance(movix_patch.get("route_proof"), dict) else {}
    live_gate = movix_patch.get("live_route_gate") if isinstance(movix_patch.get("live_route_gate"), dict) else {}
    explicit_block = (
        str(live_gate.get("completion_state") or "").casefold() == "terminal-blocked"
        or int(route_proof.get("provenRouteCount") or 0) == 0
    )

    manifest_rows = manifest.get("scrapers") if isinstance(manifest.get("scrapers"), list) else []
    movix_manifest = next(
        (row for row in manifest_rows if isinstance(row, dict) and cid(row.get("id")) == "movix"),
        None,
    )
    if not isinstance(movix_manifest, dict):
        raise SystemExit("MOVIX manifest row missing")

    # Activation is deliberately read-only here. Keep whatever publication state
    # currently exists in both the manifest and provider-overrides byte-for-byte.
    activation_before = movix_manifest.get("enabled")
    manifest_overrides = movix_patch.get("manifest_overrides")
    override_enabled_present = isinstance(manifest_overrides, dict) and "enabled" in manifest_overrides
    override_enabled_before = manifest_overrides.get("enabled") if override_enabled_present else None

    report_row = health_row(health, "movix")
    evidence = report_row.get("evidence") if isinstance(report_row.get("evidence"), dict) else {}
    report_row["enabled"] = movix_manifest.get("enabled") is not False

    if not proven_routes and explicit_block:
        report_row["action"] = ROUTE_PROOF_DIAGNOSTIC_ACTION
        report_row["failed_gates"] = [ROUTE_PROOF_FAILED_GATE]
        report_row["observed_status"] = "no-proven-route"
        evidence.update({
            "authority": ROUTE_PROOF_AUTHORITY,
            "provider_id": "movix",
            "route_proof_version": 5,
            "proven_route_count": 0,
            "status": "no-proven-route",
            "activation_destructive": False,
        })
        report_row["evidence"] = evidence
        state = "diagnostic-no-proven-route"
    else:
        if str(report_row.get("action") or "") in {
            ROUTE_PROOF_DIAGNOSTIC_ACTION,
            LEGACY_ROUTE_PROOF_DISABLE_ACTION,
        }:
            report_row["action"] = "route-proof-present-preserve-activation"
            report_row["failed_gates"] = [
                value for value in report_row.get("failed_gates") or []
                if str(value) != ROUTE_PROOF_FAILED_GATE
            ]
        evidence.update({
            "authority": ROUTE_PROOF_AUTHORITY,
            "provider_id": "movix",
            "route_proof_version": 5,
            "proven_route_count": len(proven_routes),
            "status": str(movix_proof.get("status") or "proven"),
            "activation_destructive": False,
        })
        report_row["evidence"] = evidence
        state = "proof-present-preserve-activation"

    # Fail closed if this diagnostic owner ever starts mutating activation again.
    if movix_manifest.get("enabled") != activation_before:
        raise SystemExit("route proof attempted to mutate MOVIX manifest activation")
    manifest_overrides_after = movix_patch.get("manifest_overrides")
    override_enabled_present_after = isinstance(manifest_overrides_after, dict) and "enabled" in manifest_overrides_after
    override_enabled_after = manifest_overrides_after.get("enabled") if override_enabled_present_after else None
    if (override_enabled_present_after, override_enabled_after) != (override_enabled_present, override_enabled_before):
        raise SystemExit("route proof attempted to mutate MOVIX override activation")

    patches["movix"] = movix_patch
    overrides["provider_patches"] = patches
    write(args.manifest, manifest)
    write(args.overrides, overrides)
    write(args.health_report, health)

    print(
        "ROUTE_PROOF_MANIFEST_POLICY_V1_OK "
        f"movix_routes={len(proven_routes)} movix_enabled={str(movix_manifest.get('enabled')).lower()} "
        f"state={state} activation_mutated=false health_action={report_row.get('action')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
