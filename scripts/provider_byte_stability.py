#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Raw provider-byte stability verifier.

Provider optimization/minification is deliberately disabled while NiakVIO runtime
semantics are being stabilized. This module is the single Deep/native/publication byte-validation boundary and it never rewrites JavaScript bytes.

Every checked artifact is validated structurally/syntactically, hashed, and
returned byte-for-byte. Core START/END Lego ownership therefore cannot be altered
by a formatter/minifier in this phase.
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
VALIDATOR = ROOT / "scripts/validate_provider_artifact.cjs"
BYTE_STABILITY_VERSION = "raw-v1"

RUNTIME_DOMAIN_PREFIX = "/* NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1 */"
ADAPTIVE_DOMAIN_BEGIN = "/* NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1:BEGIN */"
ADAPTIVE_DOMAIN_END = "/* NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1:END */"
CORE_START_BOUNDARY = "/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */"
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
    return text[:cursor].encode("utf-8"), text[cursor:].encode("utf-8")


def split_provider_core_tail(data: bytes) -> tuple[bytes, bytes]:
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return data, b""
    boundary = text.find(CORE_START_BOUNDARY)
    if boundary < 0:
        return data, b""
    provider = text[:boundary].encode("utf-8")
    core_tail = text[boundary:].encode("utf-8")
    if not provider.strip() or not core_tail.strip():
        return data, b""
    return provider, core_tail


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
        details = "\n".join(
            part.strip() for part in (completed.stdout, completed.stderr)
            if part and part.strip()
        )
        raise RuntimeError(
            f"raw provider artifact rejected by validator ({completed.returncode}): "
            f"{details[-1600:]}"
        )


def _validate_bytes(data: bytes) -> None:
    data.decode("utf-8", errors="strict")
    with tempfile.TemporaryDirectory(prefix="niakvio-provider-raw-", dir=ROOT) as temp:
        path = Path(temp) / "provider.js"
        path.write_bytes(data)
        validate_artifact(path)


def verify_bytes(data: bytes) -> tuple[bytes, dict[str, Any]]:
    """Validate and return the exact input bytes without any JS transformation."""
    _validate_bytes(data)
    digest = sha256(data)
    prefix, body = split_owned_prefix_bootstraps(data)
    _provider, core_tail = split_provider_core_tail(body)
    report = {
        "schemaVersion": 4,
        "tool": "raw-bytes",
        "toolVersion": BYTE_STABILITY_VERSION,
        "phase": "provider-byte-stability-v1",
        "mode": "raw-preserve",
        "mangle": False,
        "conservativeCompression": False,
        "riskFlags": [],
        "applied": False,
        "reason": "javascript_transform_disabled_until_runtime_stable",
        "fixedPointVerified": True,
        "sourceSha256": digest,
        "candidateSha256": digest,
        "bytesBefore": len(data),
        "bytesAfter": len(data),
        "bytesSaved": 0,
        "savingPercent": 0.0,
        "sizeReduced": False,
        "ownedPrefixPreserved": bool(prefix),
        "ownedPrefixBytes": len(prefix),
        "coreTailPreserved": bool(core_tail),
        "coreTailBytes": len(core_tail),
        "requiresRuntimeRetest": True,
    }
    return data, report


def verify_file(path: Path) -> dict[str, Any]:
    original = path.resolve().read_bytes()
    chosen, report = verify_bytes(original)
    if chosen != original:
        raise AssertionError("raw-byte verifier must never rewrite provider bytes")
    return report


def verify_candidate(stage: Path, candidate: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    local_path = str(candidate.get("local_path") or "").strip()
    if not local_path:
        raise ValueError("candidate local_path is required")
    stage = stage.resolve()
    path = (stage / local_path).resolve()
    path.relative_to((stage / "providers").resolve())
    if not path.is_file():
        raise FileNotFoundError(path)
    current = path.read_bytes()
    expected = str(candidate.get("sha256") or "").strip().casefold()
    actual = sha256(current)
    if expected and actual != expected:
        raise ValueError(f"candidate hash mismatch before byte-stability check: {candidate.get('key')}")
    chosen, report = verify_bytes(current)
    if chosen != current:
        raise AssertionError("raw-byte verifier must never rewrite repair candidate")
    updated = dict(candidate)
    updated["byte_stability"] = report
    return updated, report


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def verify_registry(stage: Path, report_path: Path) -> dict[str, Any]:
    stage = stage.resolve()
    registry_path = stage / "candidates.json"
    registry = load_json(registry_path)
    candidates = [row for row in registry.get("candidates") or [] if isinstance(row, dict)]
    output_candidates: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        updated, report = verify_candidate(stage, candidate)
        output_candidates.append(updated)
        rows.append({
            "key": candidate.get("key"),
            "provider": candidate.get("canonical_id"),
            **report,
        })
    registry["candidates"] = output_candidates
    registry["provider_byte_stability"] = {
        "schema_version": 1,
        "phase": "provider-byte-stability-v1",
        "tool": "raw-bytes",
        "tool_version": BYTE_STABILITY_VERSION,
        "transform_enabled": False,
        "candidate_count": len(rows),
        "validated_count": len(rows),
        "requires_deep_retest": True,
    }
    registry.pop("provider_purification", None)
    write_json(registry_path, registry)
    payload = {
        "schemaVersion": 1,
        "phase": "provider-byte-stability-v1",
        "tool": "raw-bytes",
        "toolVersion": BYTE_STABILITY_VERSION,
        "transformEnabled": False,
        "candidateCount": len(rows),
        "appliedCount": 0,
        "bytesSaved": 0,
        "savingPercent": 0.0,
        "runtimeProofRequired": True,
        "rows": rows,
    }
    write_json(report_path.resolve(), payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, default=ROOT / "staging")
    parser.add_argument("--report", type=Path, default=ROOT / "health-output/provider-byte-stability.json")
    args = parser.parse_args()
    payload = verify_registry(args.stage, args.report)
    print(
        "FIELD_PROVIDER_BYTE_STABILITY "
        f"candidates={payload['candidateCount']} validated={payload['candidateCount']} "
        "transform_enabled=false bytes_rewritten=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
