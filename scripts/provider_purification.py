#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Conservative provider JS purification shared by deep and Brain repair paths.

Purification is never accepted as proof by itself. The transformed artifact is
validated syntactically/structurally here, then the existing deep/native reader
pipelines must prove it again before publication or repair acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PURIFIER = ROOT / "engine_v2/scripts/purify-provider.mjs"
VALIDATOR = ROOT / "scripts/validate_provider_artifact.cjs"
TERSER_VERSION = "5.50.0"
_TERSER_READY = False


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ensure_terser() -> None:
    """Install the exact build-only purifier dependency when absent.

    Terser is deliberately not a provider runtime dependency. Keeping it out of
    package.json avoids shipping a build tool into Nuvio; deep/Brain pipelines
    install the exact pinned version in their ephemeral workspace only.
    """
    global _TERSER_READY
    if _TERSER_READY:
        return
    package_path = ROOT / "node_modules/terser/package.json"
    try:
        payload = json.loads(package_path.read_text(encoding="utf-8"))
        if str(payload.get("version") or "") == TERSER_VERSION:
            _TERSER_READY = True
            return
    except (OSError, json.JSONDecodeError):
        pass

    completed = subprocess.run(
        [
            "npm", "install",
            "--ignore-scripts", "--no-audit", "--no-fund",
            "--no-save", "--package-lock=false",
            f"terser@{TERSER_VERSION}",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    if completed.returncode != 0:
        details = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part and part.strip())
        raise RuntimeError(f"unable to install pinned Terser {TERSER_VERSION}: {details[-1800:]}")
    try:
        payload = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("pinned Terser install completed but package metadata is unavailable") from exc
    if str(payload.get("version") or "") != TERSER_VERSION:
        raise RuntimeError(f"pinned Terser install resolved unexpected version {payload.get('version')!r}")
    _TERSER_READY = True


def _extract_result(stdout: str) -> dict[str, Any]:
    marker = "NIAKVIO_PURIFICATION_RESULT="
    lines = [line for line in stdout.splitlines() if line.startswith(marker)]
    if not lines:
        raise RuntimeError("purifier returned no structured result")
    payload = json.loads(lines[-1][len(marker):])
    if not isinstance(payload, dict):
        raise RuntimeError("purifier result is not an object")
    if str(payload.get("toolVersion") or "") != TERSER_VERSION:
        raise RuntimeError(f"unexpected Terser version: {payload.get('toolVersion')!r}")
    if payload.get("mangle") is not False:
        raise RuntimeError("phase-1 provider purification must never mangle identifiers")
    return payload


def validate_artifact(path: Path) -> None:
    completed = subprocess.run(
        ["node", str(VALIDATOR), str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    if completed.returncode != 0:
        details = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part and part.strip())
        raise RuntimeError(f"purified provider rejected by validator ({completed.returncode}): {details[-1600:]}")


def purify_bytes(data: bytes) -> tuple[bytes, dict[str, Any]]:
    ensure_terser()
    before_sha = sha256(data)
    with tempfile.TemporaryDirectory(prefix="niakvio-provider-purify-") as temp:
        temp_dir = Path(temp)
        input_path = temp_dir / "input.js"
        output_path = temp_dir / "output.js"
        input_path.write_bytes(data)
        completed = subprocess.run(
            ["node", str(PURIFIER), "--input", str(input_path), "--output", str(output_path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
        if completed.returncode != 0:
            details = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part and part.strip())
            raise RuntimeError(f"Terser provider purification failed ({completed.returncode}): {details[-1800:]}")
        result = _extract_result(completed.stdout)
        purified = output_path.read_bytes()
        validate_artifact(output_path)

    after_sha = sha256(purified)
    applied = purified != data and len(purified) < len(data)
    chosen = purified if applied else data
    chosen_sha = after_sha if applied else before_sha
    report = {
        **result,
        "applied": applied,
        "reason": "size_reduced_and_valid" if applied else "no_safe_size_gain",
        "sourceSha256": before_sha,
        "candidateSha256": chosen_sha,
        "bytesBefore": len(data),
        "bytesAfter": len(chosen),
        "bytesSaved": max(0, len(data) - len(chosen)),
        "savingPercent": round(max(0, len(data) - len(chosen)) * 100 / max(1, len(data)), 2),
        "validator": "validate_provider_artifact.cjs",
        "requiresRuntimeRetest": True,
    }
    return chosen, report


def purify_file(path: Path) -> dict[str, Any]:
    path = path.resolve()
    original = path.read_bytes()
    chosen, report = purify_bytes(original)
    if report["applied"]:
        path.write_bytes(chosen)
    return report


def purify_candidate(stage: Path, candidate: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    local_path = str(candidate.get("local_path") or "").strip()
    if not local_path:
        raise ValueError("candidate local_path is required")
    stage = stage.resolve()
    path = (stage / local_path).resolve()
    path.relative_to((stage / "providers").resolve())
    if not path.is_file():
        raise FileNotFoundError(path)

    current = path.read_bytes()
    expected = str(candidate.get("sha256") or "")
    if expected and sha256(current) != expected:
        raise ValueError(f"candidate hash mismatch before purification: {candidate.get('key')}")

    chosen, report = purify_bytes(current)
    updated = dict(candidate)
    if report["applied"]:
        path.write_bytes(chosen)
        updated["sha256"] = report["candidateSha256"]
        updated["bytes"] = len(chosen)
        patches = list(updated.get("local_patches") or [])
        patches.append({
            "type": "provider_purification",
            "phase": "post-transform",
            "revision": 1,
            "tool": "terser",
            "tool_version": TERSER_VERSION,
            "mangle": False,
            "conservative_compression": bool(report.get("conservativeCompression")),
            "risk_flags": list(report.get("riskFlags") or []),
            "source_sha256": report["sourceSha256"],
            "output_sha256": report["candidateSha256"],
            "bytes_before": report["bytesBefore"],
            "bytes_after": report["bytesAfter"],
        })
        updated["local_patches"] = patches
    updated["purification"] = report
    return updated, report


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def purify_registry(stage: Path, report_path: Path) -> dict[str, Any]:
    stage = stage.resolve()
    registry_path = stage / "candidates.json"
    registry = load_json(registry_path)
    candidates = [row for row in registry.get("candidates") or [] if isinstance(row, dict)]
    output_candidates: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    total_before = 0
    total_after = 0

    for candidate in candidates:
        updated, report = purify_candidate(stage, candidate)
        output_candidates.append(updated)
        total_before += int(report["bytesBefore"])
        total_after += int(report["bytesAfter"])
        rows.append({
            "key": candidate.get("key"),
            "provider": candidate.get("canonical_id"),
            **report,
        })

    registry["candidates"] = output_candidates
    registry["provider_purification"] = {
        "schema_version": 1,
        "phase": "provider-purification-v1",
        "tool": "terser",
        "tool_version": TERSER_VERSION,
        "mangle": False,
        "candidate_count": len(rows),
        "applied_count": sum(1 for row in rows if row["applied"]),
        "bytes_before": total_before,
        "bytes_after": total_after,
        "bytes_saved": max(0, total_before - total_after),
        "requires_deep_retest": True,
        "repair_candidates_must_repurify": True,
    }
    write_json(registry_path, registry)

    payload = {
        "schemaVersion": 1,
        "phase": "provider-purification-v1",
        "tool": "terser",
        "toolVersion": TERSER_VERSION,
        "mangle": False,
        "candidateCount": len(rows),
        "appliedCount": sum(1 for row in rows if row["applied"]),
        "riskyFormattingOnlyCount": sum(1 for row in rows if row.get("riskFlags")),
        "bytesBefore": total_before,
        "bytesAfter": total_after,
        "bytesSaved": max(0, total_before - total_after),
        "savingPercent": round(max(0, total_before - total_after) * 100 / max(1, total_before), 2),
        "runtimeProofRequired": True,
        "rows": rows,
    }
    write_json(report_path.resolve(), payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, default=ROOT / "staging")
    parser.add_argument("--report", type=Path, default=ROOT / "health-output/provider-purification.json")
    args = parser.parse_args()
    payload = purify_registry(args.stage, args.report)
    print(
        "FIELD_PROVIDER_PURIFICATION "
        f"candidates={payload['candidateCount']} applied={payload['appliedCount']} "
        f"risky={payload['riskyFormattingOnlyCount']} bytes_saved={payload['bytesSaved']} "
        f"saving_percent={payload['savingPercent']} mangle=false runtime_retest_required=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
