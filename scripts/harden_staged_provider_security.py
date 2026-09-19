#!/usr/bin/env python3
"""Verify mandatory provider-wide security hardening on a staged registry.

Provider/Core composition owns all byte mutation before this step. This stage is
therefore fail-closed and validation-only: if the deterministic security transform
would change a staged bundle, composition is incomplete and publication stops.
Generated Core Lego bytes are never rewritten here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from provider_patches.global_provider_security_hardening_v1 import harden_bundle

ROOT = Path(__file__).resolve().parents[1]

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


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

        current_text = current.decode("utf-8", errors="strict")
        hardened_text, report = harden_bundle(current_text)
        if hardened_text != current_text:
            raise ValueError(
                f"staged candidate is not security-normalized before validation: {row.get('key')}"
            )
        already += 1

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
        "requires_runtime_retest": False,
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
        f"console={summary['console_shadows']} runtime_retest_required=false validation_only=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
