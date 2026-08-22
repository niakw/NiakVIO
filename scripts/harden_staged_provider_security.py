#!/usr/bin/env python3
"""Apply mandatory provider-wide security hardening to a staged registry.

This is a deterministic pre-runtime normalization. It never decides whether a
provider is healthy or publishable; it only rewrites known unsafe code shapes,
validates the resulting JavaScript, updates content hashes, and leaves the
existing Brain/health/native gates to accept or reject the artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from provider_security_hardening import assert_hardened, harden_bytes

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_provider_artifact.cjs"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def _validate(path: Path) -> None:
    completed = subprocess.run(
        ["node", str(VALIDATOR), str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    if completed.returncode:
        details = "\n".join(
            part.strip() for part in (completed.stdout, completed.stderr)
            if part and part.strip()
        )
        raise RuntimeError(f"security-hardened provider rejected by validator: {details[-1600:]}")


def harden_stage(stage: Path) -> dict[str, Any]:
    stage = stage.resolve()
    registry_path = stage / "candidates.json"
    registry = _load(registry_path)
    rows = [row for row in registry.get("candidates") or [] if isinstance(row, dict)]
    applied = 0
    already = 0
    structured = 0
    literal = 0
    hosts = 0
    consoles = 0

    for row in rows:
        relative = str(row.get("local_path") or "").strip()
        if not relative:
            raise ValueError(f"candidate has no local_path: {row.get('key')}")
        path = (stage / relative).resolve()
        path.relative_to((stage / "providers").resolve())
        if not path.is_file():
            raise FileNotFoundError(path)

        current = path.read_bytes()
        expected = str(row.get("sha256") or "")
        if expected and sha256(current) != expected:
            raise ValueError(f"candidate hash mismatch before security hardening: {row.get('key')}")

        hardened, report = harden_bytes(current)
        if report.get("alreadyHardened"):
            already += 1
        if hardened != current:
            path.write_bytes(hardened)
            try:
                _validate(path)
                assert_hardened(hardened.decode("utf-8", errors="strict"))
            except Exception:
                path.write_bytes(current)
                raise
            output_sha = sha256(hardened)
            row["sha256"] = output_sha
            row["bytes"] = len(hardened)
            patches = list(row.get("local_patches") or [])
            patches.append({
                "type": "provider_security_hardening",
                "phase": "pre-runtime",
                "revision": 1,
                "scope": "global",
                "source_sha256": sha256(current),
                "output_sha256": output_sha,
                "structured_parse_changes": int(report.get("structuredParseChanges") or 0),
                "literal_decode_changes": int(report.get("literalDecodeChanges") or 0),
                "hostname_changes": int(report.get("hostnameChanges") or 0),
                "console_shadow": bool(report.get("consoleShadow")),
            })
            row["local_patches"] = patches
            applied += 1
        else:
            assert_hardened(current.decode("utf-8", errors="strict"))

        structured += int(report.get("structuredParseChanges") or 0)
        literal += int(report.get("literalDecodeChanges") or 0)
        hosts += int(report.get("hostnameChanges") or 0)
        consoles += int(bool(report.get("consoleShadow")))

    summary = {
        "schema_version": 1,
        "phase": "provider-security-hardening-v1",
        "scope": "all-staged-candidates",
        "candidate_count": len(rows),
        "applied_count": applied,
        "already_hardened_count": already,
        "structured_parse_changes": structured,
        "literal_decode_changes": literal,
        "hostname_changes": hosts,
        "console_shadows": consoles,
        "requires_runtime_retest": True,
    }
    registry["provider_security_hardening"] = summary
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, default=ROOT / "staging")
    args = parser.parse_args()
    summary = harden_stage(args.stage)
    print(
        "FIELD_PROVIDER_SECURITY_HARDENING "
        f"candidates={summary['candidate_count']} applied={summary['applied_count']} "
        f"already={summary['already_hardened_count']} structured={summary['structured_parse_changes']} "
        f"literal={summary['literal_decode_changes']} hosts={summary['hostname_changes']} "
        f"console={summary['console_shadows']} runtime_retest_required=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
