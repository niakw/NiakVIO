#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Conservative provider JS purification shared by deep and Brain repair paths.

Purification is never accepted as proof by itself. The transformed artifact is
validated syntactically/structurally here, then the existing deep/native reader
pipelines must prove it again before publication or repair acceptance.

NiakVIO-owned *prefix* bootstraps are deliberately kept outside Terser. They are
rebuild boundaries, not provider source. Letting a formatter relocate their
NUVIO comments makes the next Core pass lose ownership of the corresponding
statement and can accumulate a second bootstrap. The provider/Core body is still
fully purified and byte-fixed-point; the small generated prefix is preserved in
its canonical source form and then the complete artifact is runtime-tested by the
normal Deep/native gates.
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

RUNTIME_DOMAIN_PREFIX = "/* NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1 */"
ADAPTIVE_DOMAIN_BEGIN = "/* NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1:BEGIN */"
ADAPTIVE_DOMAIN_END = "/* NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1:END */"
RUNTIME_DOMAIN_CALL = '})(typeof globalThis!=="undefined"?globalThis:this,'


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _consume_owned_newline(text: str, index: int) -> int:
    if text[index:index + 2] == "\r\n":
        return index + 2
    if text[index:index + 1] in {"\r", "\n"}:
        return index + 1
    return index


def _canonical_runtime_prefix_end(text: str, start: int) -> int | None:
    """Return the end of our canonical runtime-domain prefix statement.

    This parser is intentionally used *before* Terser sees the generated prefix.
    Therefore the exact invocation anchor is an ownership proof rather than a
    heuristic over third-party JavaScript.
    """
    if not text.startswith(RUNTIME_DOMAIN_PREFIX, start):
        return None
    call = text.find(RUNTIME_DOMAIN_CALL, start + len(RUNTIME_DOMAIN_PREFIX))
    if call < 0:
        return None
    end = text.find(");", call + len(RUNTIME_DOMAIN_CALL))
    if end < 0:
        return None
    return _consume_owned_newline(text, end + 2)


def _canonical_adaptive_prefix_end(text: str, start: int) -> int | None:
    if not text.startswith(ADAPTIVE_DOMAIN_BEGIN, start):
        return None
    end = text.find(ADAPTIVE_DOMAIN_END, start + len(ADAPTIVE_DOMAIN_BEGIN))
    if end < 0:
        return None
    return _consume_owned_newline(text, end + len(ADAPTIVE_DOMAIN_END))


def split_owned_prefix_bootstraps(data: bytes) -> tuple[bytes, bytes]:
    """Split only canonical NiakVIO prefix wrappers from provider/Core body bytes."""
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return b"", data
    cursor = 0
    while cursor < len(text):
        end = _canonical_runtime_prefix_end(text, cursor)
        if end is None:
            end = _canonical_adaptive_prefix_end(text, cursor)
        if end is None or end <= cursor:
            break
        cursor = end
    if cursor <= 0:
        return b"", data
    prefix = text[:cursor].encode("utf-8")
    body = text[cursor:].encode("utf-8")
    if not body.strip():
        # Never feed an empty/non-provider body into a build transform.
        return b"", data
    return prefix, body


def ensure_terser() -> None:
    """Install the exact build-only purifier dependency when absent."""
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


def _run_purifier(data: bytes, *, format_only: bool) -> tuple[bytes, dict[str, Any]]:
    """Run one pinned-Terser pass and validate the resulting provider/Core body."""
    ensure_terser()
    with tempfile.TemporaryDirectory(prefix="niakvio-provider-purify-", dir=ROOT) as temp:
        temp_dir = Path(temp)
        input_path = temp_dir / "input.js"
        output_path = temp_dir / "output.js"
        input_path.write_bytes(data)
        command = ["node", str(PURIFIER), "--input", str(input_path), "--output", str(output_path)]
        if format_only:
            command.append("--format-only")
        completed = subprocess.run(
            command,
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
    return purified, result


def _stable_candidate(data: bytes, *, format_only: bool) -> tuple[bytes, dict[str, Any], bool, str | None]:
    """Return a candidate only when an identical second Terser pass validates."""
    first, result = _run_purifier(data, format_only=format_only)
    try:
        second, _second_result = _run_purifier(first, format_only=format_only)
    except Exception as exc:
        return first, result, False, f"second_pass_error:{type(exc).__name__}:{exc}"
    if second != first:
        return first, result, False, "second_pass_bytes_changed"
    return first, result, True, None


def _has_mandatory_boundary_cleanup(result: dict[str, Any]) -> bool:
    """Whether a stable candidate contains required NiakVIO boundary cleanup.

    Boundary canonicalization is correctness metadata normalization, not a size
    optimization. It must survive candidate selection even when the canonical
    spelling is byte-neutral or slightly larger than the source representation.
    """
    if str(result.get("mode") or "") == "boundary-canonicalization":
        return True
    if bool(result.get("retainedAudioBoundaryCanonicalized")):
        return True
    return int(result.get("floatedGeneratedMarkersCanonicalized") or 0) > 0


def _change_reason(data: bytes, chosen: bytes, result: dict[str, Any]) -> str:
    if chosen == data:
        return "no_safe_fixed_point_size_gain"
    if _has_mandatory_boundary_cleanup(result):
        return "boundary_canonicalized_valid_and_fixed_point"
    if len(chosen) < len(data):
        return "size_reduced_valid_and_fixed_point"
    return "stable_transform_valid_and_fixed_point"


def _purify_body_bytes(data: bytes) -> tuple[bytes, dict[str, Any]]:
    """Purify bytes that contain provider/Core code but no owned prefix wrapper."""
    before_sha = sha256(data)
    fallback_reason: str | None = None
    selected_mode = "original"
    selected_result: dict[str, Any] = {
        "schemaVersion": 2,
        "tool": "terser",
        "toolVersion": TERSER_VERSION,
        "phase": "provider-purification-v1",
        "mode": "original",
        "mangle": False,
        "conservativeCompression": False,
        "riskFlags": [],
        "bytesBefore": len(data),
        "bytesAfter": len(data),
    }
    chosen = data
    fixed_point_verified = True

    try:
        compressed, compressed_result, stable, reason = _stable_candidate(data, format_only=False)
    except Exception as exc:
        compressed = data
        compressed_result = selected_result
        stable = False
        reason = f"first_pass_error:{type(exc).__name__}:{exc}"

    compressed_required = _has_mandatory_boundary_cleanup(compressed_result)
    if stable and (compressed == data or len(compressed) < len(data) or compressed_required):
        chosen = compressed
        selected_result = compressed_result
        selected_mode = str(compressed_result.get("mode") or "conservative-compression")
    else:
        fallback_reason = reason or (
            "compression_size_growth_without_mandatory_cleanup"
            if stable else "compression_not_fixed_point"
        )
        try:
            formatted, formatted_result, format_stable, format_reason = _stable_candidate(data, format_only=True)
        except Exception as exc:
            formatted = data
            formatted_result = selected_result
            format_stable = False
            format_reason = f"format_first_pass_error:{type(exc).__name__}:{exc}"
        formatted_required = _has_mandatory_boundary_cleanup(formatted_result)
        if format_stable and (formatted == data or len(formatted) < len(data) or formatted_required):
            chosen = formatted
            selected_result = formatted_result
            selected_mode = str(formatted_result.get("mode") or "format-only")
        else:
            chosen = data
            selected_mode = "original"
            fixed_point_verified = True
            fallback_reason = f"{fallback_reason};{format_reason or 'format_size_growth_without_mandatory_cleanup'}"

    chosen_sha = sha256(chosen)
    applied = chosen != data
    report = {
        **selected_result,
        "mode": selected_mode,
        "applied": applied,
        "reason": _change_reason(data, chosen, selected_result),
        "fallbackReason": fallback_reason,
        "fixedPointVerified": fixed_point_verified,
        "sourceSha256": before_sha,
        "candidateSha256": chosen_sha,
        "bytesBefore": len(data),
        "bytesAfter": len(chosen),
        "bytesSaved": max(0, len(data) - len(chosen)),
        "savingPercent": round(max(0, len(data) - len(chosen)) * 100 / max(1, len(data)), 2),
        "sizeReduced": len(chosen) < len(data),
        "boundaryCanonicalized": _has_mandatory_boundary_cleanup(selected_result),
        "validator": "validate_provider_artifact.cjs",
        "requiresRuntimeRetest": True,
    }
    return chosen, report


def purify_bytes(data: bytes) -> tuple[bytes, dict[str, Any]]:
    """Purify provider/Core bytes while preserving canonical owned prefix bootstraps.

    The returned *complete* artifact is itself byte-idempotent under this function:
    the prefix is reproduced byte-for-byte and only the provider/Core body crosses
    the Terser boundary.
    """
    prefix, body = split_owned_prefix_bootstraps(data)
    if not prefix:
        return _purify_body_bytes(data)

    purified_body, body_report = _purify_body_bytes(body)
    chosen = prefix + purified_body
    applied = chosen != data
    report = {
        **body_report,
        "applied": applied,
        "reason": _change_reason(data, chosen, body_report),
        "sourceSha256": sha256(data),
        "candidateSha256": sha256(chosen),
        "bytesBefore": len(data),
        "bytesAfter": len(chosen),
        "bytesSaved": max(0, len(data) - len(chosen)),
        "savingPercent": round(max(0, len(data) - len(chosen)) * 100 / max(1, len(data)), 2),
        "sizeReduced": len(chosen) < len(data),
        "ownedPrefixPreserved": True,
        "ownedPrefixBytes": len(prefix),
        "fixedPointVerified": bool(body_report.get("fixedPointVerified", True)),
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
            "revision": 3,
            "tool": "terser",
            "tool_version": TERSER_VERSION,
            "mode": report.get("mode"),
            "mangle": False,
            "fixed_point_verified": True,
            "conservative_compression": bool(report.get("conservativeCompression")),
            "risk_flags": list(report.get("riskFlags") or []),
            "source_sha256": report["sourceSha256"],
            "output_sha256": report["candidateSha256"],
            "bytes_before": report["bytesBefore"],
            "bytes_after": report["bytesAfter"],
            "owned_prefix_preserved": bool(report.get("ownedPrefixPreserved")),
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
        "schema_version": 3,
        "phase": "provider-purification-v1",
        "tool": "terser",
        "tool_version": TERSER_VERSION,
        "mangle": False,
        "fixed_point_required": True,
        "owned_prefix_bootstraps_outside_terser": True,
        "candidate_count": len(rows),
        "applied_count": sum(1 for row in rows if row["applied"]),
        "format_only_count": sum(1 for row in rows if row.get("mode") == "format-only"),
        "bytes_before": total_before,
        "bytes_after": total_after,
        "bytes_saved": max(0, total_before - total_after),
        "requires_deep_retest": True,
        "repair_candidates_must_repurify": True,
    }
    write_json(registry_path, registry)

    payload = {
        "schemaVersion": 3,
        "phase": "provider-purification-v1",
        "tool": "terser",
        "toolVersion": TERSER_VERSION,
        "mangle": False,
        "fixedPointRequired": True,
        "ownedPrefixBootstrapsOutsideTerser": True,
        "candidateCount": len(rows),
        "appliedCount": sum(1 for row in rows if row["applied"]),
        "formatOnlyCount": sum(1 for row in rows if row.get("mode") == "format-only"),
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
        f"format_only={payload['formatOnlyCount']} risky={payload['riskyFormattingOnlyCount']} "
        f"bytes_saved={payload['bytesSaved']} saving_percent={payload['savingPercent']} "
        "mangle=false fixed_point_required=true owned_prefixes_outside_terser=true runtime_retest_required=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())