#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Validate NiakVIO's durable Core byte-stability contract.

JavaScript optimization/minification is intentionally disabled while provider
runtime semantics are stabilized. This contract is validation-only: Core
composition owns deterministic START/END Lego blocks and publication validates
the exact post-Core bytes without rewriting them.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPLY = ROOT / "scripts" / "apply_provider_overrides.py"
REAPPLY = ROOT / "scripts" / "reapply_published_overrides.py"
SECURITY_HOOK = ROOT / "scripts" / "provider_patches" / "global_provider_security_hardening_v1.py"
BYTE_STABILITY = ROOT / "scripts" / "provider_byte_stability.py"
BYTE_STABILITY_TEST = ROOT / "tests" / "provider_byte_stability_contract_test.py"

CORE_START_MARKER = "NUVIO_GLOBAL_CORE_START_BOUNDARY_V1"
SECURITY_BOUNDARY = "__nuvioGlobalProviderSecurityBoundaryV1"


def assert_contract() -> None:
    apply_text = APPLY.read_text(encoding="utf-8")
    reapply_text = REAPPLY.read_text(encoding="utf-8")
    security_text = SECURITY_HOOK.read_text(encoding="utf-8")
    byte_text = BYTE_STABILITY.read_text(encoding="utf-8")
    byte_test = BYTE_STABILITY_TEST.read_text(encoding="utf-8")

    for required in (
        f'CORE_START_MARKER = "{CORE_START_MARKER}"',
        "def _provider_export_floor(text: str) -> int:",
        'boundary_needle = f"/* {CORE_START_MARKER} */"',
        "provider_floor = _provider_export_floor(text)",
        'text.find(boundary_needle, provider_floor) < 0',
        "validate_managed_fixes(result)",
    ):
        assert required in apply_text, f"missing Core composition contract: {required}"

    for required in (
        "from provider_byte_stability import BYTE_STABILITY_VERSION, verify_bytes",
        "verified_bytes, byte_stability = verify_bytes(patched)",
        "if verified_bytes != patched:",
        '"tool": "raw-bytes"',
        "BYTE_STABILITY_VERSION",
        "digest = hashlib.sha256(patched).hexdigest()",
    ):
        assert required in reapply_text, f"missing raw publication contract: {required}"

    assert "provider_purification" not in reapply_text
    assert "purify_bytes" not in reapply_text
    assert not (ROOT / "scripts/provider_purification.py").exists()
    assert not (ROOT / "engine_v2/scripts/purify-provider.mjs").exists()
    assert not (ROOT / "engine_v2/scripts/terser-clean.mjs").exists()

    for required in (
        'BYTE_STABILITY_VERSION = "raw-v1"',
        'VALIDATOR = ROOT / "scripts/validate_provider_artifact.cjs"',
        "def verify_bytes(data: bytes)",
        "def verify_file(path: Path)",
        "def verify_candidate(stage: Path, candidate: dict[str, Any])",
        "def verify_registry(stage: Path, report_path: Path)",
        '"transform_enabled": False',
    ):
        assert required in byte_text, f"missing byte-stability contract: {required}"

    for required in (
        'MANAGED_FIX_ID = "CORE.PROVIDER_SECURITY_BOUNDARY.V1"',
        f'HOOK_BOUNDARY = "{SECURITY_BOUNDARY}"',
        "replace_managed_fix(",
    ):
        assert required in security_text, f"missing managed security boundary: {required}"

    for required in (
        "assert not (ROOT / \"engine_v2/scripts/purify-provider.mjs\").exists()",
        "assert not (ROOT / \"engine_v2/scripts/terser-clean.mjs\").exists()",
        'assert first_report["tool"] == "raw-bytes"',
        'assert first_report["applied"] is False',
    ):
        assert required in byte_test, f"missing raw-byte regression proof: {required}"


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()

    # Validation-only by design. There is no code formatter/optimizer to
    # materialize here; the composer and publisher own exact bytes directly.
    assert_contract()
    print(
        "FIELD_CORE_FIXED_POINT_CONTRACT "
        "changed=0 core_start_boundary=managed-lego raw_bytes=raw-v1 "
        "javascript_transform=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
