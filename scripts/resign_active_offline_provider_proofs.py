#!/usr/bin/env python3
"""Rebind active live-unverified activation proofs to exact current provider bytes.

This is deliberately weaker than runtime validation. It never promotes a provider
to FULL OK and never manufactures playback evidence. It only refreshes the static
exact-byte contract after deterministic Provider-v3 rematerialization changes a
content-addressed provider artifact.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from activate_bulk_proven_providers import pending_artifact_digest
from activate_bulk_offline_proven_providers import contract_ok, node_syntax_ok
from provider_base_store import (
    provider_model_has_executable_plan,
    provider_model_has_identity_execution_plan,
)
from provider_patch_blocks import decode_managed_data

ROOT = Path(__file__).resolve().parents[1]
MODE = "bulk_offline_contract_live_unverified"
BLOCKER = "live_native_validation_pending"
NETWORK = "not_authoritative_in_github_waf_limited"


def load(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def canon(value: object) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", str(value or "").strip().casefold()).strip("-")


def active_rows(root: Path) -> dict[str, tuple[dict[str, Any], str]]:
    out: dict[str, tuple[dict[str, Any], str]] = {}
    global_manifest = load(root / "manifest.json", {})
    for row in global_manifest.get("scrapers") or []:
        if isinstance(row, dict) and row.get("enabled") is not False and canon(row.get("id")):
            out[canon(row.get("id"))] = (row, "global")
    vf_manifest = load(root / "vf" / "manifest.json", {})
    for row in vf_manifest.get("scrapers") or []:
        pid = canon(row.get("id")) if isinstance(row, dict) else ""
        if pid and row.get("enabled") is not False and pid not in out:
            out[pid] = (row, "france")
    return out


def resolve_artifact(root: Path, filename: object) -> tuple[Path, str]:
    relative = str(filename or "").strip().replace("\\", "/")
    if relative.startswith("../"):
        relative = relative[3:]
    if not relative.startswith("providers/"):
        raise RuntimeError(f"active offline proof requires providers/** artifact, got {relative!r}")
    path = (root / relative).resolve()
    if root.resolve() not in path.parents or not path.is_file():
        raise RuntimeError(f"provider artifact missing or outside repository: {relative}")
    return path, relative


def rebind_one(
    root: Path,
    pid: str,
    row: dict[str, Any],
    scope: str,
    provenance_row: dict[str, Any],
) -> dict[str, Any]:
    if provenance_row.get("activation_mode") != MODE or provenance_row.get("check_mode") != MODE:
        raise RuntimeError(f"{pid}: not an offline-contract activation")
    if provenance_row.get("check_status") != "live_unverified":
        raise RuntimeError(f"{pid}: offline proof status is not live_unverified")
    if provenance_row.get("activation_eligible") is not True:
        raise RuntimeError(f"{pid}: offline activation is not eligible")
    if provenance_row.get("strict_activation_eligible") is not False:
        raise RuntimeError(f"{pid}: strict activation must remain false")
    if provenance_row.get("runtime_evidence_eligible") is not False:
        raise RuntimeError(f"{pid}: runtime evidence must remain false")
    if list(provenance_row.get("activation_blockers") or []) != [BLOCKER]:
        raise RuntimeError(f"{pid}: unexpected offline activation blockers")

    proof = provenance_row.get("bulk_offline_activation_proof")
    if not isinstance(proof, dict) or proof.get("schemaVersion") != 1:
        raise RuntimeError(f"{pid}: exact-byte offline proof missing")
    if proof.get("scope") != scope:
        raise RuntimeError(f"{pid}: proof scope mismatch expected={scope} actual={proof.get('scope')}")
    if proof.get("networkValidation") != NETWORK:
        raise RuntimeError(f"{pid}: unexpected network proof authority")
    if proof.get("livePlaybackValidated") is not False or proof.get("fullOkClaimed") is not False:
        raise RuntimeError(f"{pid}: offline proof must never claim runtime/FULL validation")

    artifact, relative = resolve_artifact(root, row.get("filename"))
    digest = pending_artifact_digest(artifact)
    syntax_ok, syntax_detail = node_syntax_ok(artifact)
    if not syntax_ok:
        raise RuntimeError(f"{pid}: node syntax failed: {syntax_detail}")
    valid_contract, missing = contract_ok(pid, artifact)
    if not valid_contract:
        raise RuntimeError(f"{pid}: Provider-v3 contract missing: {','.join(missing)}")

    text = artifact.read_text(encoding="utf-8", errors="strict")
    model = decode_managed_data(text, f"PROVIDER.{pid.upper()}.CONFIG.V1")
    if not provider_model_has_executable_plan(model):
        raise RuntimeError(f"{pid}: executable provider plan missing")
    if not provider_model_has_identity_execution_plan(model):
        raise RuntimeError(f"{pid}: identity execution plan missing")

    previous = str(proof.get("providerSha256") or "").strip().casefold()
    provenance_row["published_filename"] = relative
    provenance_row["sha256"] = digest
    provenance_row["patched_sha256"] = digest

    minimizer = provenance_row.get("pending_minimizer")
    if isinstance(minimizer, dict):
        if minimizer.get("fixedPoint") is not True:
            raise RuntimeError(f"{pid}: previous minimizer contract is not fixed-point")
        minimizer["sha256"] = digest

    proof["providerSha256"] = digest
    proof["pendingSha256"] = digest
    proof["minimizerFixedPoint"] = True
    proof["nodeSyntax"] = "passed"
    proof["providerV3Contract"] = "passed"
    proof["providerExecutablePlan"] = "passed"
    proof["providerIdentityExecutionPlan"] = "passed"
    proof["directOriginSyntax"] = "passed"
    proof["networkValidation"] = NETWORK
    proof["livePlaybackValidated"] = False
    proof["fullOkClaimed"] = False

    return {
        "provider": pid,
        "scope": scope,
        "filename": relative,
        "previousSha256": previous,
        "providerSha256": digest,
        "changed": previous != digest,
        "livePlaybackValidated": False,
        "fullOkClaimed": False,
    }


def rebind(root: Path, requested: set[str] | None = None, *, apply: bool) -> dict[str, Any]:
    provenance_path = root / "PROVENANCE.json"
    provenance = load(provenance_path, {})
    prov_rows = provenance.get("providers")
    if not isinstance(prov_rows, dict):
        raise RuntimeError("PROVENANCE.json providers map missing")

    rows = active_rows(root)
    selected: list[tuple[str, dict[str, Any], str, dict[str, Any]]] = []
    for pid, (row, scope) in sorted(rows.items()):
        prov = prov_rows.get(pid)
        if not isinstance(prov, dict) or prov.get("activation_mode") != MODE:
            continue
        if requested is not None and pid not in requested:
            continue
        selected.append((pid, row, scope, prov))

    if requested is not None:
        missing = sorted(requested - {pid for pid, *_ in selected})
        if missing:
            raise RuntimeError("requested active offline providers not eligible: " + ",".join(missing))
    if not selected:
        raise RuntimeError("no active offline-contract providers selected")

    results = [rebind_one(root, pid, row, scope, prov) for pid, row, scope, prov in selected]
    if apply:
        write(provenance_path, provenance)

    return {
        "schemaVersion": 1,
        "mode": MODE,
        "providerCount": len(results),
        "changedCount": sum(1 for row in results if row["changed"]),
        "apply": apply,
        "providers": results,
        "runtimePromotion": False,
        "fullOkClaimed": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--providers", default="")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    requested = {canon(v) for v in str(args.providers or "").split(",") if canon(v)}
    result = rebind(ROOT, requested or None, apply=bool(args.apply))
    print(
        "FIELD_ACTIVE_OFFLINE_PROOF_REBOUND "
        f"providers={result['providerCount']} changed={result['changedCount']} "
        f"apply={str(result['apply']).lower()} full_ok=false runtime_promotion=false"
    )
    for row in result["providers"]:
        print(
            "FIELD_ACTIVE_OFFLINE_PROOF_PROVIDER "
            f"provider={row['provider']} scope={row['scope']} changed={str(row['changed']).lower()} "
            f"sha256={row['providerSha256']} file={row['filename']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
