#!/usr/bin/env python3
"""Build the non-publishing Brain recovery queue for lifecycle-disabled providers.

Production disablement and Brain learning are separate authorities. Providers
auto-disabled because the current architecture regressed or is nonfunctional
stay disabled in manifests, but their exact retained bytes remain eligible for
isolated Brain/Learning experiments. Manual/security/removed/shutdown disables
are intentionally excluded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ELIGIBLE_PREFIXES = (
    "auto_off_current_architecture_regression",
    "auto_off_current_architecture_nonfunctional",
)


def load(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def cid(value: Any) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest_rows(root: Path, relative: str, scope: str) -> dict[str, dict[str, Any]]:
    payload = load(root / relative, {})
    out: dict[str, dict[str, Any]] = {}
    for row in payload.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        provider = cid(row.get("id"))
        if not provider:
            continue
        item = dict(row)
        item["_scope"] = scope
        out[provider] = item
    return out


def managed_asset(root: Path, row: dict[str, Any]) -> Path:
    raw = str(row.get("filename") or "").strip().replace("\\", "/")
    while raw.startswith("../"):
        raw = raw[3:]
    path = (root / raw).resolve()
    disabled = (root / "provider-disabled").resolve()
    if path.parent != disabled or not path.is_file():
        raise ValueError(f"{cid(row.get('id'))}: disabled recovery asset invalid: {raw}")
    return path


def build(root: Path) -> dict[str, Any]:
    lifecycle = load(root / "automation/provider-disabled-lifecycle.json", {})
    disabled_state = lifecycle.get("disabled") if isinstance(lifecycle, dict) else {}
    if not isinstance(disabled_state, dict):
        disabled_state = {}
    archived = lifecycle.get("archived") if isinstance(lifecycle, dict) else {}
    archived_ids = {cid(k) for k in archived} if isinstance(archived, dict) else set()

    global_rows = manifest_rows(root, "manifest.json", "global")
    france_rows = manifest_rows(root, "vf/manifest.json", "france")
    census = load(root / "automation/provider-census-status.json", {})
    census_rows = {
        cid(row.get("provider")): row
        for row in (census.get("providers") or [])
        if isinstance(row, dict) and cid(row.get("provider"))
    }

    providers: list[dict[str, Any]] = []
    for raw_provider, state in sorted(disabled_state.items()):
        provider = cid(raw_provider)
        if not provider or provider in archived_ids or not isinstance(state, dict):
            continue
        reason = str(state.get("reason") or "").strip()
        if not reason.startswith(ELIGIBLE_PREFIXES):
            continue
        if str(state.get("state") or "") != "disabled-retained":
            continue

        rows = [
            row for row in (global_rows.get(provider), france_rows.get(provider))
            if isinstance(row, dict)
        ]
        if not rows:
            continue
        if any(row.get("enabled") is not False for row in rows):
            # Recovery queue is never an alternate execution authority.
            continue

        assets: dict[str, str] = {}
        for row in rows:
            asset = managed_asset(root, row)
            assets[str(asset.relative_to(root))] = sha256(asset)
        if len(assets) != 1:
            raise ValueError(f"{provider}: projection asset disagreement: {sorted(assets)}")
        asset_path, asset_sha = next(iter(assets.items()))
        current = census_rows.get(provider) or {}
        family = (
            "current-architecture-regression"
            if reason.startswith("auto_off_current_architecture_regression")
            else "current-architecture-nonfunctional"
        )
        providers.append({
            "provider": provider,
            "family": family,
            "disabledReason": reason,
            "disabledAt": state.get("disabledAt"),
            "purgeAfter": state.get("purgeAfter"),
            "scopes": sorted({str(row.get("_scope")) for row in rows}),
            "asset": asset_path,
            "assetSha256": asset_sha,
            "lastCensusStatus": current.get("status"),
            "lastDominantIssue": current.get("dominantIssue"),
            "lastLaneVerdicts": current.get("latestLaneVerdicts"),
            "brainLabEligible": True,
            "productionExecutionAllowed": False,
            "publicationAllowed": False,
        })

    return {
        "schemaVersion": 1,
        "authority": "brain-disabled-recovery-lab-v1",
        "sourceLifecycleUpdatedAt": lifecycle.get("updatedAt") if isinstance(lifecycle, dict) else None,
        "sourceCensusRunId": census.get("runId") if isinstance(census, dict) else None,
        "proofAuthority": False,
        "executionAuthority": False,
        "publicationAuthority": False,
        "eligibleReasonPrefixes": list(ELIGIBLE_PREFIXES),
        "eligibleCount": len(providers),
        "providers": providers,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "automation/provider-disabled-recovery-queue.json",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    payload = build(root)
    output = args.output if args.output.is_absolute() else root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "PROVIDER_DISABLED_RECOVERY_QUEUE "
        f"eligible={payload['eligibleCount']} proof=false execution=false publication=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
