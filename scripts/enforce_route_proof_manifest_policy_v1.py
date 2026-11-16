#!/usr/bin/env python3
"""Project current route-proof evidence into health diagnostics without owning activation.

Route proof owns route/DATA confidence only. Publication activation belongs to the
current Global+France catalogue/finalization transaction. This helper therefore:

* derives current publication membership from the Global+France projection union
  when operating on the repository manifest;
* limits health updates to the targeted repair cohort when the merged report exposes
  `portfolioRepair.targetedProviders`;
* never writes manifest or provider-overrides bytes;
* records proven/no-proven-route state as diagnostic evidence only.

The historical filename is retained for workflow compatibility; there is no
provider-specific policy in this implementation.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from current_provider_scope import projection_visible_provider_ids, projection_visible_provider_rows  # noqa: E402

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


def manifest_rows(value: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        cid(row.get("id")): dict(row)
        for row in value.get("scrapers") or []
        if isinstance(row, dict) and cid(row.get("id"))
    }


def publication_rows(manifest_path: Path, manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if manifest_path.resolve() == DEFAULT_MANIFEST.resolve():
        rows = {
            cid(row.get("id")): dict(row)
            for row in projection_visible_provider_rows()
            if isinstance(row, dict) and cid(row.get("id"))
        }
        expected = projection_visible_provider_ids()
        if set(rows) != expected:
            raise SystemExit(
                "route-proof publication scope drift "
                f"missing={sorted(expected-set(rows))} extra={sorted(set(rows)-expected)}"
            )
        return rows
    return manifest_rows(manifest)


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


def targeted_ids(report: dict[str, Any], recovered: dict[str, dict[str, Any]]) -> set[str]:
    portfolio = report.get("portfolioRepair") if isinstance(report.get("portfolioRepair"), dict) else {}
    explicit = {
        cid(value)
        for value in portfolio.get("targetedProviders") or []
        if cid(value)
    }
    return explicit or set(recovered)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--overrides", type=Path, default=DEFAULT_OVERRIDES)
    parser.add_argument("--health-report", type=Path, default=DEFAULT_HEALTH_REPORT)
    args = parser.parse_args()

    report = load(args.report)
    manifest = load(args.manifest)
    # Parse overrides to preserve CLI/data-contract validation, but route proof is
    # deliberately forbidden from mutating this publication-owned document.
    load(args.overrides)
    health = load(args.health_report) if args.health_report.is_file() else {"providers": []}

    recovered = {
        cid(row.get("providerId") or row.get("id") or row.get("provider")): row
        for row in report.get("providers") or []
        if isinstance(row, dict) and cid(row.get("providerId") or row.get("id") or row.get("provider"))
    }
    current = publication_rows(args.manifest, manifest)
    requested = targeted_ids(report, recovered)
    unknown = sorted(requested - set(current))
    if unknown:
        raise SystemExit("route-proof targeted providers outside current publication: " + ",".join(unknown))

    processed = proven = unresolved = missing = 0
    proof_version = int(report.get("schemaVersion") or 0)
    for provider_id in sorted(requested):
        proof = recovered.get(provider_id)
        if not isinstance(proof, dict):
            missing += 1
            continue
        processed += 1
        routes = [str(value).strip() for value in proof.get("routes") or [] if str(value).strip()]
        state = str(proof.get("status") or "").strip().casefold()
        row = health_row(health, provider_id)
        row["enabled"] = current[provider_id].get("enabled") is not False
        evidence = row.get("evidence") if isinstance(row.get("evidence"), dict) else {}

        if routes:
            proven += 1
            if str(row.get("action") or "") in {
                ROUTE_PROOF_DIAGNOSTIC_ACTION,
                LEGACY_ROUTE_PROOF_DISABLE_ACTION,
            }:
                row["action"] = "route-proof-present-preserve-activation"
            row["failed_gates"] = [
                value for value in row.get("failed_gates") or []
                if str(value) != ROUTE_PROOF_FAILED_GATE
            ]
            evidence_state = state or "proven"
        else:
            unresolved += 1
            row["action"] = ROUTE_PROOF_DIAGNOSTIC_ACTION
            failed = [str(value) for value in row.get("failed_gates") or [] if str(value)]
            if ROUTE_PROOF_FAILED_GATE not in failed:
                failed.append(ROUTE_PROOF_FAILED_GATE)
            row["failed_gates"] = failed
            row["observed_status"] = state or "no-proven-route"
            evidence_state = state or "no-proven-route"

        evidence.update({
            "authority": ROUTE_PROOF_AUTHORITY,
            "provider_id": provider_id,
            "route_proof_version": proof_version,
            "proven_route_count": len(routes),
            "status": evidence_state,
            "activation_destructive": False,
        })
        row["evidence"] = evidence

    write(args.health_report, health)
    print(
        "ROUTE_PROOF_MANIFEST_POLICY_V1_OK "
        f"targeted={len(requested)} processed={processed} proven={proven} "
        f"unresolved={unresolved} missing={missing} activation_mutated=false "
        "scope=current-publication provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
