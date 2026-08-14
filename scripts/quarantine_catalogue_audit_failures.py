#!/usr/bin/env python3
"""Publish fail-safe inert bundles for providers with conclusive catalogue/media audit failures.

The quarantine is deliberately publication-scoped: it is recorded in the
manifest/provenance/health transaction, not in provider-overrides.json. New
upstream candidates therefore remain testable on the next deep run and can
recover automatically once they prove correct content again.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
PROVENANCE = ROOT / "PROVENANCE.json"
HEALTH_REPORT = ROOT / "health-report.json"
QUARANTINE_PATCH = ROOT / "scripts" / "provider_patches" / "quarantine_provider_v1.py"
QUARANTINE_MARKER = "NUVIO_PROVIDER_QUARANTINE_V1"
BLOCKER = "catalogue_audit_playable_identity_contradiction"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bump_patch(value: Any) -> str:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", str(value or "").strip())
    if not match:
        return "1.0.1"
    major, minor, patch = map(int, match.groups())
    return f"{major}.{minor}.{patch + 1}"


def safe_id(value: str) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", value.casefold()).strip(".-") or "provider"


def load_quarantine_apply():
    spec = importlib.util.spec_from_file_location("nuvio_audit_quarantine", QUARANTINE_PATCH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load quarantine patch: {QUARANTINE_PATCH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


def conclusive_rows(audit: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in audit.get("rows") or []:
        if not isinstance(row, dict):
            continue
        wrong = int(row.get("identity_contradiction_count") or 0) > 0
        false_positive = row.get("playable_identity_false_positive") is True
        broken_hls = int(row.get("hls_variant_failures") or 0) > 0 or int(row.get("hls_audio_failures") or 0) > 0
        if not (wrong or false_positive or broken_hls):
            continue
        provider_id = str(row.get("provider_id") or "").strip().casefold()
        if provider_id:
            grouped.setdefault(provider_id, []).append(row)
    return grouped


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", required=True)
    parser.add_argument("--evidence")
    parser.add_argument("--workflow-run-id", type=int, default=0)
    parser.add_argument("--tested-commit-sha", default="")
    args = parser.parse_args()

    audit_path = Path(args.audit).resolve()
    audit = load(audit_path)
    failures = conclusive_rows(audit)
    if not failures:
        print("catalogue audit quarantine: no conclusive failures")
        return 0

    manifest = load(MANIFEST)
    provenance = load(PROVENANCE)
    health = load(HEALTH_REPORT)
    manifest_rows = {
        str(row.get("id") or "").strip().casefold(): row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }
    provenance_rows = provenance.setdefault("providers", {})
    if not isinstance(provenance_rows, dict):
        raise ValueError("PROVENANCE providers must be an object")
    health_rows = {
        str(row.get("id") or "").strip().casefold(): row
        for row in health.get("providers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }

    missing_manifest = sorted(set(failures) - set(manifest_rows))
    missing_health = sorted(set(failures) - set(health_rows))
    if missing_manifest:
        raise SystemExit("audit quarantine providers missing from manifest: " + ", ".join(missing_manifest))
    if missing_health:
        raise SystemExit("audit quarantine providers missing from health report: " + ", ".join(missing_health))

    apply_quarantine = load_quarantine_apply()
    referenced_before = {
        str(row.get("filename") or "")
        for row in manifest_rows.values()
        if str(row.get("filename") or "")
    }
    old_candidates: list[Path] = []

    for provider_id, evidence_rows in sorted(failures.items()):
        entry = manifest_rows[provider_id]
        old_relative = str(entry.get("filename") or "").strip()
        old_path = (ROOT / old_relative).resolve()
        if not old_relative.startswith("providers/") or not old_path.is_file():
            raise SystemExit(f"{provider_id}: unsafe or missing current bundle: {old_relative}")
        old_sha = file_sha(old_path)
        reason = BLOCKER
        inert = str(apply_quarantine(old_path.read_text(encoding="utf-8"), {"reason": reason}))
        if QUARANTINE_MARKER not in inert or reason not in inert:
            raise SystemExit(f"{provider_id}: quarantine patch did not produce an inert marker")
        payload = inert.encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        new_relative = f"providers/{safe_id(provider_id)}--nuvio-audit-quarantine--{digest[:16]}.js"
        new_path = ROOT / new_relative
        new_path.parent.mkdir(parents=True, exist_ok=True)
        new_path.write_bytes(payload)

        entry["filename"] = new_relative
        entry["enabled"] = False
        entry["version"] = bump_patch(entry.get("version"))

        provider_provenance = provenance_rows.setdefault(provider_id, {})
        if not isinstance(provider_provenance, dict):
            provider_provenance = {}
            provenance_rows[provider_id] = provider_provenance
        provider_provenance["published_filename"] = new_relative
        provider_provenance["sha256"] = digest
        provider_provenance["patched_sha256"] = digest
        provider_provenance["activation_eligible"] = False
        provider_provenance["strict_activation_eligible"] = False
        provider_provenance["strict_grace_eligible"] = False
        provider_provenance["historical_quality_grace_eligible"] = False
        provider_provenance["runtime_evidence_eligible"] = False
        provider_provenance["activation_mode"] = "catalogue_audit_safety_quarantine"
        blockers = [str(value) for value in provider_provenance.get("activation_blockers") or [] if str(value)]
        if BLOCKER not in blockers:
            blockers.append(BLOCKER)
        provider_provenance["activation_blockers"] = blockers
        local_patches = list(provider_provenance.get("local_patches") or [])
        audit_record = {
            "type": "safety_quarantine",
            "phase": "publication",
            "source": "catalogue_media_audit",
            "reason": reason,
            "workflow_run_id": int(args.workflow_run_id or 0),
            "tested_commit_sha": str(args.tested_commit_sha or ""),
            "tested_filename": old_relative,
            "tested_sha256": old_sha,
            "fixtures": sorted({str(row.get("fixture") or "") for row in evidence_rows if str(row.get("fixture") or "")}),
            "identity_contradictions": sum(int(row.get("identity_contradiction_count") or 0) for row in evidence_rows),
            "playable_streams": sum(int(row.get("playable_stream_count") or 0) for row in evidence_rows),
        }
        local_patches = [
            row for row in local_patches
            if not (isinstance(row, dict) and row.get("type") == "safety_quarantine" and row.get("source") == "catalogue_media_audit")
        ]
        local_patches.append(audit_record)
        provider_provenance["local_patches"] = local_patches

        health_row = health_rows[provider_id]
        health_row["enabled"] = False
        health_row["action"] = "published-disabled-failed-gates"
        failed_gates = [str(value) for value in health_row.get("failed_gates") or [] if str(value)]
        if BLOCKER not in failed_gates:
            failed_gates.append(BLOCKER)
        health_row["failed_gates"] = failed_gates
        health_row["catalogue_audit_quarantine"] = {
            "reason": reason,
            "tested_filename": old_relative,
            "tested_sha256": old_sha,
            "quarantined_filename": new_relative,
            "quarantined_sha256": digest,
            "fixtures": audit_record["fixtures"],
            "identity_contradictions": audit_record["identity_contradictions"],
            "playable_streams": audit_record["playable_streams"],
        }
        old_candidates.append(old_path)
        print(
            f"catalogue audit quarantine: {provider_id} fixtures={','.join(audit_record['fixtures'])} "
            f"contradictions={audit_record['identity_contradictions']} -> {new_relative}"
        )

    write(MANIFEST, manifest)
    write(PROVENANCE, provenance)
    write(HEALTH_REPORT, health)

    subprocess.run(["python", "scripts/generate_language_manifests.py"], cwd=ROOT, check=True)
    subprocess.run(["python", "scripts/sync_release_versions.py", "--manifest", "manifest.json"], cwd=ROOT, check=True)
    subprocess.run(["python", "scripts/prune_unreferenced_providers.py"], cwd=ROOT, check=True)
    subprocess.run(["python", "scripts/validate_language_projection.py"], cwd=ROOT, check=True)

    # Old unsafe bundles may remain only if another authoritative reference still
    # needs them. Never delete a shared/reference-held artifact here.
    current_manifest = load(MANIFEST)
    referenced_after = {
        str(row.get("filename") or "")
        for row in current_manifest.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("filename") or "")
    }
    for old_path in old_candidates:
        try:
            relative = old_path.relative_to(ROOT).as_posix()
        except ValueError:
            continue
        if relative not in referenced_after and relative in referenced_before and old_path.is_file():
            # prune_unreferenced_providers owns deletion. This branch is only a
            # diagnostic assertion that the unsafe path is no longer live.
            print(f"catalogue audit quarantine: superseded bundle retained only by non-manifest state: {relative}")

    if args.evidence:
        evidence = Path(args.evidence).resolve()
        subprocess.run([
            "python", "scripts/release_evidence_fence.py", "fingerprint",
            "--manifest", "manifest.json", "--root", ".", "--output", str(evidence),
        ], cwd=ROOT, check=True)

    print(f"catalogue audit quarantine complete: providers={len(failures)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
