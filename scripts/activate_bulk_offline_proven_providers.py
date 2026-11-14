#!/usr/bin/env python3
"""Activate a bulk onboarding cohort from exact-byte offline Provider v3 proof.

This path exists for environments where GitHub-hosted network checks are not
authoritative because WAF / anti-bot layers can reject CI egress. It never calls
an offline proof FULL OK and never claims live playback. Every activated provider
remains explicitly live-unverified until a WAF-capable/native replay proves it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from activate_bulk_proven_providers import pending_artifact_digest, restore_pending_artifacts

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
CATALOG = ROOT / "provider_catalog.json"
OVERRIDES = ROOT / "provider-overrides.json"
PROVENANCE = ROOT / "PROVENANCE.json"
HUBS = ROOT / "provider-hubs.json"
STAGE = ROOT / "automation/provider-bulk-onboarding-stage.json"
REQUEST = ROOT / ".github/provider-onboarding/batch.json"
OUTPUT = ROOT / "automation/provider-bulk-offline-activation-latest.json"
MODE = "bulk_offline_contract_live_unverified"
BLOCKER = "live_native_validation_pending"


def load(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", str(value or "").strip().casefold()).strip("-")


def node_syntax_ok(path: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        ["node", "--check", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    detail = (proc.stdout + proc.stderr).strip()
    return proc.returncode == 0, detail[-1200:]


def contract_ok(provider_id: str, path: Path) -> tuple[bool, list[str]]:
    text = path.read_text(encoding="utf-8", errors="strict")
    required = {
        "provider_id": f"/* NIAKVIO_PROVIDER_ID:{provider_id} */",
        "owned_v3": "/* NIAKVIO_PROVIDER_BASE_OWNED_V3 */",
        "data_model": "NIAKVIO_PROVIDER_MODEL",
    }
    missing = [name for name, marker in required.items() if marker not in text]
    return not missing, missing


def main() -> int:
    ap = argparse.ArgumentParser(description="Activate exact bulk bytes with offline Provider v3 proof only")
    ap.add_argument("--stage", type=Path, default=STAGE)
    ap.add_argument("--request", type=Path, default=REQUEST)
    ap.add_argument("--output", type=Path, default=OUTPUT)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    request = load(args.request, {})
    if not isinstance(request, dict) or request.get("activationPolicy") != MODE:
        raise RuntimeError(f"request must explicitly opt into activationPolicy={MODE}")
    validation = request.get("validationPolicy")
    if not isinstance(validation, dict):
        raise RuntimeError("offline activation request lacks validationPolicy")
    required_policy = {
        "githubNetworkFailuresAreInconclusive": True,
        "offlineContractRequired": True,
        "exactByteProofRequired": True,
        "nodeSyntaxRequired": True,
        "providerV3ContractRequired": True,
        "liveNativeValidationStillRequiredForFullOk": True,
        "neverPromoteOfflineProofToFullOk": True,
    }
    for key, expected in required_policy.items():
        if validation.get(key) is not expected:
            raise RuntimeError(f"offline activation policy must keep {key}={expected!r}")

    stage = load(args.stage, {})
    if not isinstance(stage, dict) or stage.get("mode") != "staged-disabled-pending":
        raise RuntimeError("bulk onboarding stage summary is missing or not pending")
    staged = [row for row in stage.get("providers") or [] if isinstance(row, dict)]
    if not staged or len(staged) != int(stage.get("providerCount") or 0):
        raise RuntimeError("bulk onboarding stage provider count mismatch")

    requested_rows = {
        norm(row.get("id") or row.get("provider")): row
        for row in request.get("providers") or []
        if isinstance(row, dict) and norm(row.get("id") or row.get("provider"))
    }
    if set(requested_rows) != {norm(row.get("id")) for row in staged}:
        raise RuntimeError("request/stage provider identity set mismatch")

    manifest = load(MANIFEST, {"scrapers": []})
    catalog = load(CATALOG, {"providers": []})
    overrides = load(OVERRIDES, {})
    provenance = load(PROVENANCE, {"providers": {}})
    hubs = load(HUBS, {"providers": {}})

    manifest_map = {
        norm(row.get("id")): row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and norm(row.get("id"))
    }
    catalog_map = {
        norm(entry.get("canonicalId") or ((entry.get("scraper") or {}).get("id") if isinstance(entry.get("scraper"), dict) else "")): entry
        for entry in catalog.get("providers") or []
        if isinstance(entry, dict)
    }
    prov_map = provenance.get("providers") if isinstance(provenance.get("providers"), dict) else {}
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    capabilities = overrides.get("provider_capabilities") if isinstance(overrides.get("provider_capabilities"), dict) else {}
    hub_map = hubs.get("providers") if isinstance(hubs.get("providers"), dict) else {}

    activated: list[str] = []
    blocked: list[dict[str, Any]] = []
    proof_rows: list[dict[str, Any]] = []

    for staged_row in staged:
        pid = norm(staged_row.get("id"))
        scope = str(staged_row.get("scope") or "").strip().casefold()
        request_row = requested_rows.get(pid) or {}
        if scope not in {"global", "france"}:
            blocked.append({"provider": pid, "reason": "invalid_scope", "scope": scope})
            continue

        manifest_row = manifest_map.get(pid)
        catalog_entry = catalog_map.get(pid)
        if scope == "france":
            if not isinstance(catalog_entry, dict):
                blocked.append({"provider": pid, "reason": "france_catalog_entry_missing"})
                continue
            projections = catalog_entry.get("projections") if isinstance(catalog_entry.get("projections"), dict) else {}
            if projections.get("general") is not False or projections.get("vf") is not True:
                blocked.append({"provider": pid, "reason": "france_projection_not_exclusive"})
                continue
            manifest_row = catalog_entry.get("scraper")
        elif not isinstance(manifest_row, dict):
            blocked.append({"provider": pid, "reason": "global_manifest_entry_missing"})
            continue

        patch = patches.get(pid)
        prov = prov_map.get(pid)
        if not isinstance(manifest_row, dict) or not isinstance(patch, dict) or not isinstance(prov, dict):
            blocked.append({"provider": pid, "reason": "canonical_provider_state_missing"})
            continue
        if manifest_row.get("enabled") is not False:
            blocked.append({"provider": pid, "reason": "provider_not_pending_disabled"})
            continue
        if str(prov.get("activation_mode") or "") != "bulk_onboarding_pending":
            blocked.append({"provider": pid, "reason": "provenance_not_bulk_pending"})
            continue

        filename = str(manifest_row.get("filename") or "").strip()
        local_filename = filename[3:] if filename.startswith("../") else filename
        if not local_filename.startswith("provider-disabled/"):
            blocked.append({"provider": pid, "reason": "pending_path_not_disabled", "filename": filename})
            continue
        pending_path = (ROOT / local_filename).resolve()
        if not pending_path.is_file():
            blocked.append({"provider": pid, "reason": "pending_provider_missing", "filename": local_filename})
            continue

        try:
            exact_sha = pending_artifact_digest(pending_path)
        except Exception as exc:
            blocked.append({"provider": pid, "reason": "pending_not_minimizer_fixed_point", "detail": str(exc)})
            continue
        staged_sha = str(staged_row.get("pendingSha256") or "").strip().casefold()
        recorded_sha = str(prov.get("sha256") or "").strip().casefold()
        if not re.fullmatch(r"[0-9a-f]{64}", staged_sha) or exact_sha != staged_sha:
            blocked.append({"provider": pid, "reason": "stage_exact_byte_hash_mismatch"})
            continue
        if recorded_sha and exact_sha != recorded_sha:
            blocked.append({"provider": pid, "reason": "provenance_exact_byte_hash_mismatch"})
            continue

        syntax_ok, syntax_detail = node_syntax_ok(pending_path)
        if not syntax_ok:
            blocked.append({"provider": pid, "reason": "node_syntax_failed", "detail": syntax_detail})
            continue
        valid_contract, missing_contract = contract_ok(pid, pending_path)
        if not valid_contract:
            blocked.append({"provider": pid, "reason": "provider_v3_contract_missing", "missing": missing_contract})
            continue

        direct = str(request_row.get("direct") or request_row.get("direct_url") or "").strip()
        if not re.match(r"^https?://[^/\s]+", direct):
            blocked.append({"provider": pid, "reason": "direct_public_origin_missing"})
            continue

        try:
            active_relative = restore_pending_artifacts(pid, manifest_row, prov, dry_run=args.dry_run)
        except RuntimeError as exc:
            blocked.append({"provider": pid, "reason": "pending_artifact_state_invalid", "detail": str(exc)})
            continue

        active_path = ROOT / active_relative
        active_sha = exact_sha if args.dry_run else hashlib.sha256(active_path.read_bytes()).hexdigest()
        if active_sha != exact_sha:
            raise RuntimeError(f"{pid}: activation changed exact provider bytes")

        manifest_row["enabled"] = True
        patch.setdefault("manifest_overrides", {})["enabled"] = True
        notes = patch.setdefault("notes", [])
        offline_note = (
            "Activated from exact-byte offline Provider v3 contract proof because GitHub-hosted "
            "network/WAF checks are non-authoritative; live native validation remains pending."
        )
        if offline_note not in notes:
            notes.append(offline_note)
        capability = capabilities.get(pid)
        if isinstance(capability, dict):
            capability["validation"] = MODE
        hub = hub_map.get(pid)
        if isinstance(hub, dict):
            hub["manifest_status"] = "Active"

        prov["check_mode"] = MODE
        prov["check_status"] = "live_unverified"
        prov["activation_eligible"] = True
        prov["strict_activation_eligible"] = False
        prov["runtime_evidence_eligible"] = False
        prov["activation_mode"] = MODE
        prov["activation_blockers"] = [BLOCKER]
        proof = {
            "schemaVersion": 1,
            "scope": scope,
            "providerSha256": active_sha,
            "pendingSha256": staged_sha,
            "minimizerFixedPoint": True,
            "nodeSyntax": "passed",
            "providerV3Contract": "passed",
            "directOriginSyntax": "passed",
            "networkValidation": "not_authoritative_in_github_waf_limited",
            "livePlaybackValidated": False,
            "fullOkClaimed": False,
            "inventorySource": str(request.get("source") or ""),
            "inventoryRank": request_row.get("inventory_rank"),
            "inventoryScore": request_row.get("inventory_score"),
        }
        prov["bulk_offline_activation_proof"] = proof
        activated.append(pid)
        proof_rows.append({"provider": pid, **proof})

    if blocked:
        payload = {
            "schemaVersion": 1,
            "mode": MODE,
            "requestedCount": len(staged),
            "activationCount": len(activated),
            "blockedCount": len(blocked),
            "blockedProviders": blocked,
            "dryRun": bool(args.dry_run),
        }
        write(args.output, payload)
        raise RuntimeError(f"offline activation is atomic: {len(blocked)} provider(s) failed proof")

    payload = {
        "schemaVersion": 1,
        "mode": MODE,
        "requestedCount": len(staged),
        "activationCount": len(activated),
        "activationScopes": {
            "global": sum(1 for row in staged if str(row.get("scope") or "").casefold() == "global"),
            "france": sum(1 for row in staged if str(row.get("scope") or "").casefold() == "france"),
        },
        "providers": proof_rows,
        "networkPolicy": (
            "GitHub-hosted WAF/network failures are inconclusive. This proof covers exact generated bytes, "
            "syntax and Provider v3 contract only; FULL OK still requires live/native validation."
        ),
        "dryRun": bool(args.dry_run),
    }
    if not args.dry_run:
        write(MANIFEST, manifest)
        write(CATALOG, catalog)
        write(OVERRIDES, overrides)
        write(PROVENANCE, provenance)
        write(HUBS, hubs)
    write(args.output, payload)
    print(
        "PROVIDER_BULK_OFFLINE_ACTIVATION "
        f"requested={len(staged)} activated={len(activated)} global={payload['activationScopes']['global']} "
        f"france={payload['activationScopes']['france']} live_validation=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
