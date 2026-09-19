#!/usr/bin/env python3
"""Classify HTTP 451 as runner/network blocking, not provider route invalidity.

451 (Unavailable For Legal Reasons) is explicit evidence that the request reached
an HTTP policy boundary. It must not validate a route or provider, but a run made
only of 451 responses may advance as `terminal-blocked` exactly like a 403-only
runner, while preserving the stable executable plan for another network/client.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "validate_provider_v3_routes_sequential.py"
MARKER = "PROVIDER_V3_HTTP_BLOCK_CLASSIFICATION_V1"


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False

    old = "BLOCKED_STATUSES = {401, 403, 407, 429}"
    new = (
        "# PROVIDER_V3_HTTP_BLOCK_CLASSIFICATION_V1\n"
        "# 451 is an explicit policy/jurisdiction block. It is never positive route\n"
        "# proof, but a 451-only traversal is terminal-blocked rather than broken.\n"
        "BLOCKED_STATUSES = {401, 403, 407, 429, 451}"
    )
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"blocked-status anchor count={count}")
    text = text.replace(old, new, 1)
    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str) -> None:
    if MARKER not in text:
        raise AssertionError("HTTP block classification marker missing")
    if "BLOCKED_STATUSES = {401, 403, 407, 429, 451}" not in text:
        raise AssertionError("HTTP 451 is not classified as blocked")
    if "BLOCKED_STATUSES = {401, 403, 407, 429}" in text:
        raise AssertionError("old blocked status set remains")


def main() -> int:
    changed = patch()
    print(
        "PROVIDER_V3_HTTP_BLOCK_CLASSIFICATION_V1_OK "
        f"changed={str(changed).lower()} status451=terminal-blocked-not-validated"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
