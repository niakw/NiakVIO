#!/usr/bin/env python3
"""Validate final published-provider security ordering without rewriting JS bytes.

Security hardening is independent from activation/quarantine state and must run
after provider/runtime/quarantine composition but before raw-byte validation,
content addressing and publication. JavaScript optimization/minification remains
disabled while NiakVIO runtime semantics are being stabilized.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REAPPLY = ROOT / "scripts" / "reapply_published_overrides.py"
SECURITY_IMPORT = "from provider_security_hardening import assert_hardened, harden_bytes"
BYTE_IMPORT = "from provider_byte_stability import BYTE_STABILITY_VERSION, verify_bytes"
MARKER = "all-published-provider-security-finalization-v1"


def assert_contract(text: str) -> None:
    required = (
        SECURITY_IMPORT,
        BYTE_IMPORT,
        MARKER,
        "security_hardened, security_report = harden_bytes(patched)",
        '"scope": "all-published-providers"',
        'assert_hardened(patched.decode("utf-8", errors="strict"))',
        "verified_bytes, byte_stability = verify_bytes(patched)",
        "if verified_bytes != patched:",
        '"tool": "raw-bytes"',
        "BYTE_STABILITY_VERSION",
        "digest = hashlib.sha256(patched).hexdigest()",
    )
    for value in required:
        if value not in text:
            raise AssertionError(f"missing published security finalization contract: {value}")

    forbidden = (
        "provider_purification",
        "purify_bytes",
        "purified, purification",
        '"tool": "terser"',
    )
    for value in forbidden:
        if value in text:
            raise AssertionError(f"retired provider transform contract remains: {value}")

    quarantine_replay = text.index(
        "patched, audit_quarantine_kind = publication_audit_quarantine("
    )
    terminal_state = text.index(
        'terminal_quarantine = AUDIT_QUARANTINE_MARKER.encode("utf-8") in patched'
    )
    hardening = text.index(
        "security_hardened, security_report = harden_bytes(patched)"
    )
    raw_validation = text.index(
        "verified_bytes, byte_stability = verify_bytes(patched)"
    )
    digest = text.index("digest = hashlib.sha256(patched).hexdigest()")
    if not (
        quarantine_replay
        < terminal_state
        < hardening
        < raw_validation
        < digest
    ):
        raise AssertionError(
            "published security/raw-byte ordering is not provider-state independent"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    current = REAPPLY.read_text(encoding="utf-8")
    assert_contract(current)
    print(
        "published security finalization contract is normalized "
        "raw_bytes=true javascript_transform=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
