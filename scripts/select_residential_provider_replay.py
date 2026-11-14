#!/usr/bin/env python3
"""Select current harness/network symptoms for full residential provider replay.

The transport differential is useful diagnosis, but it is not a prerequisite
for the authoritative replay: some providers fail before a safe exact GET can
be extracted, or require POST/player/session behavior only the real provider
runtime can reproduce. Once the private residential exit is confirmed active,
replay every *current* provider whose census status is environment/network
blocked and whose provider address/backend still has authority. Domain/lifecycle-
blocked providers stay out of this transport queue. The replay itself remains
the only functional authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OFFLINE_MODE = "bulk_offline_contract_live_unverified"

ELIGIBLE_STATUSES = {
    "HARNESS MISMATCH",
    "CLIENT TRANSPORT GAP",
    "HARNESS/ENV BLOCKED",
    "PROVIDER NETWORK BLOCKED",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value



def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def offline_live_unverified_transport_authority(
    root: Path,
    manifest: dict[str, Any],
    vf_manifest: dict[str, Any],
    overrides: dict[str, Any],
    activation: dict[str, Any],
) -> set[str]:
    """Return active exact-byte offline providers eligible for transport replay only.

    This does not grant Repair or playback authority. It only breaks the circular
    dependency where a WAF-limited provider must be residentially replayed before
    live authority can be established, but Repair authority is intentionally false
    until that qualification exists.
    """
    if str(activation.get("mode") or "") != OFFLINE_MODE:
        return set()

    active_rows: dict[str, dict[str, Any]] = {}
    for doc in (manifest, vf_manifest):
        for row in doc.get("scrapers") or []:
            if not isinstance(row, dict):
                continue
            pid = canon(row.get("id"))
            if not pid or row.get("enabled") is False:
                continue
            # Shared Global/VF rows must describe the same current executable.
            prior = active_rows.get(pid)
            if prior is not None and str(prior.get("filename") or "") != str(row.get("filename") or "").replace("../", ""):
                # France projection uses ../providers; normalize below instead of
                # silently accepting two different active artifacts.
                prior_name = str(prior.get("filename") or "").removeprefix("../")
                current_name = str(row.get("filename") or "").removeprefix("../")
                if prior_name != current_name:
                    continue
            active_rows[pid] = row

    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    capabilities = overrides.get("provider_capabilities") if isinstance(overrides.get("provider_capabilities"), dict) else {}
    # Current production ledger stores exact-byte activation proof rows under
    # "providers". Keep the legacy key readable for older archived ledgers, but
    # never synthesize authority when neither contains structured proof rows.
    raw_activation_rows = activation.get("providers")
    if not isinstance(raw_activation_rows, list):
        raw_activation_rows = activation.get("activatedProviders")
    if not isinstance(raw_activation_rows, list):
        raw_activation_rows = []
    activation_rows = {
        canon(row.get("provider")): row
        for row in raw_activation_rows
        if isinstance(row, dict) and canon(row.get("provider"))
    }

    allowed: set[str] = set()
    for pid, row in active_rows.items():
        capability = capabilities.get(pid) if isinstance(capabilities.get(pid), dict) else {}
        patch = patches.get(pid) if isinstance(patches.get(pid), dict) else {}
        proof = activation_rows.get(pid)
        if not isinstance(proof, dict):
            continue
        if str(capability.get("validation") or "") != OFFLINE_MODE:
            continue
        manifest_overrides = patch.get("manifest_overrides") if isinstance(patch.get("manifest_overrides"), dict) else {}
        if manifest_overrides.get("enabled") is False:
            continue
        if proof.get("minimizerFixedPoint") is not True:
            continue
        if any(str(proof.get(key) or "") != "passed" for key in (
            "nodeSyntax", "providerV3Contract", "providerExecutablePlan",
            "providerIdentityExecutionPlan", "directOriginSyntax",
        )):
            continue
        if proof.get("fullOkClaimed") is True:
            continue
        filename = str(row.get("filename") or "").strip().removeprefix("../")
        if not filename.startswith("providers/"):
            continue
        asset = root / filename
        expected = str(proof.get("providerSha256") or "").strip().casefold()
        if len(expected) != 64 or not asset.is_file() or sha256_file(asset) != expected:
            continue
        allowed.add(pid)
    return allowed

def select(
    report: dict[str, Any],
    status: dict[str, Any],
    explicit_providers: list[str] | None = None,
    offline_transport_allowed: set[str] | None = None,
) -> list[str]:
    residential = (
        report.get("residentialExitNodeEvidence")
        if isinstance(report.get("residentialExitNodeEvidence"), dict)
        else {}
    )
    if residential.get("available") is not True:
        return []

    rows = [
        row for row in status.get("providers") or []
        if isinstance(row, dict) and str(row.get("provider") or "").strip()
    ]
    transport_allowed = {canon(value) for value in (offline_transport_allowed or set()) if canon(value)}
    providers = {
        canon(row.get("provider"))
        for row in rows
        if str(row.get("status") or "") in ELIGIBLE_STATUSES
        and (row.get("authorityRepairEligible") is not False or canon(row.get("provider")) in transport_allowed)
    }

    explicit = {
        str(value or "").strip().casefold()
        for value in (explicit_providers or [])
        if str(value or "").strip()
    }
    if explicit:
        authority_allowed = {
            canon(row.get("provider"))
            for row in rows
            if row.get("authorityRepairEligible") is not False
        } | transport_allowed
        # An explicit transport qualification is itself the symptom request.
        # Allow the named current provider to full-replay through residential
        # transport even when canonical status is FULL/PARTIAL/ROUTE, while
        # still respecting current provider/address authority.
        providers.update(explicit & authority_allowed)

    return sorted(providers)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--waf", type=Path, required=True)
    ap.add_argument("--status", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--providers", default="", help="Optional comma-separated explicit current providers to full-replay regardless of canonical status")
    ap.add_argument("--manifest", type=Path, default=ROOT / "manifest.json")
    ap.add_argument("--vf-manifest", type=Path, default=ROOT / "vf/manifest.json")
    ap.add_argument("--overrides", type=Path, default=ROOT / "provider-overrides.json")
    ap.add_argument("--activation", type=Path, default=ROOT / "automation/provider-bulk-offline-activation-latest.json")
    args = ap.parse_args()

    explicit = [value.strip() for value in str(args.providers or "").split(",") if value.strip()]
    offline_allowed = offline_live_unverified_transport_authority(
        ROOT, load(args.manifest), load(args.vf_manifest), load(args.overrides), load(args.activation)
    ) if args.activation.exists() else set()
    providers = select(load(args.waf), load(args.status), explicit, offline_allowed)
    payload = {
        "schemaVersion": 2,
        "selection": "current-census-harness-network-residential-full-replay",
        "eligibleStatuses": sorted(ELIGIBLE_STATUSES),
        "providers": providers,
        "providerCount": len(providers),
        "explicitProviders": explicit,
        "offlineLiveUnverifiedTransportAuthority": sorted(offline_allowed),
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"FIELD_RESIDENTIAL_PROVIDER_REPLAY_SELECTION providers={len(providers)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
