#!/usr/bin/env python3
"""Apply explicit manifest activation policy from one completed route-proof census.

This is deliberately conservative: lack of a proven route is not a generic reason to
disable every provider. MOVIX is the explicit exception because its DATA marks the
current route plan terminal-blocked/obsolete and production reverse-rebuild policy
already requires it to stay neutralized until a real route is proved again.
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


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path}: expected object")
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--overrides", type=Path, default=DEFAULT_OVERRIDES)
    args = parser.parse_args()

    report = load(args.report)
    manifest = load(args.manifest)
    overrides = load(args.overrides)
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

    manifest_overrides = movix_patch.get("manifest_overrides")
    if not isinstance(manifest_overrides, dict):
        manifest_overrides = {}
        movix_patch["manifest_overrides"] = manifest_overrides

    if not proven_routes and explicit_block:
        movix_manifest["enabled"] = False
        manifest_overrides["enabled"] = False
        state = "disabled-no-proven-route"
    else:
        # A future positive proof may remove the route-proof quarantine, but this
        # script never force-enables MOVIX: activation still belongs to promotion.
        state = "proof-present-preserve-activation"

    patches["movix"] = movix_patch
    overrides["provider_patches"] = patches
    write(args.manifest, manifest)
    write(args.overrides, overrides)

    print(
        "ROUTE_PROOF_MANIFEST_POLICY_V1_OK "
        f"movix_routes={len(proven_routes)} movix_enabled={str(movix_manifest.get('enabled')).lower()} "
        f"state={state}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
