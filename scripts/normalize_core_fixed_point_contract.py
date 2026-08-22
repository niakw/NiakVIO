#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Verify durable Core fixed-point contracts without rewriting repository files.

The byte-level fixes are source-controlled in their owning modules.  This gate is
intentionally side-effect free: ``--apply`` and ``--check`` perform the same
assertions so CI can never enter a normalize-test-normalize loop.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPLY = ROOT / "scripts" / "apply_provider_overrides.py"
REAPPLY = ROOT / "scripts" / "reapply_published_overrides.py"
SECURITY_HOOK = ROOT / "scripts" / "provider_patches" / "global_provider_security_hardening_v1.py"
PURIFICATION = ROOT / "scripts" / "provider_purification.py"
PURIFIER = ROOT / "engine_v2" / "scripts" / "purify-provider.mjs"
PLAYBACK_TEST = ROOT / "tests" / "global_playback_integrity_policy_test.py"
PURIFICATION_TEST = ROOT / "tests" / "provider_purification_contract_test.py"

BOUNDARY = "__nuvioGlobalProviderSecurityBoundaryV1"
SECURITY_MARKER = "NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contract() -> None:
    apply_text = _read(APPLY)
    reapply_text = _read(REAPPLY)
    security_text = _read(SECURITY_HOOK)
    purification_text = _read(PURIFICATION)
    purifier_text = _read(PURIFIER)
    playback_test = _read(PLAYBACK_TEST)
    purification_test = _read(PURIFICATION_TEST)

    # Generated Core tails are rebuilt from provider-derived bytes.  The security
    # boundary is an observable JS assignment, not a relocatable comment/literal.
    for required in (
        "GENERATED_CORE_TAIL_MARKERS",
        SECURITY_MARKER,
        BOUNDARY,
        "def _strip_generated_core_tail(",
        "def _inject_runtime_domain_overrides(",
        "existing_span",
        "output = text[:existing_span[0]] + bootstrap + text[existing_span[1]:]",
    ):
        assert required in apply_text, f"missing apply fixed-point contract: {required}"

    for required in (
        f'HOOK_BOUNDARY = "{BOUNDARY}"',
        f"globalThis.{{HOOK_BOUNDARY}}=true;",
        SECURITY_MARKER,
    ):
        assert required in security_text, f"missing security boundary contract: {required}"

    # Final provider bytes: every Core/provider/runtime transform happens first,
    # then pinned Terser purification, then validation/content addressing.
    for required in (
        "from provider_purification import purify_bytes",
        "purified, purification = purify_bytes(patched)",
        '"phase": "final-post-transform"',
        '"tool": "terser"',
        '"mangle": False',
        "patched = purified",
        "digest = hashlib.sha256(patched).hexdigest()",
    ):
        assert required in reapply_text, f"missing final publication contract: {required}"
    assert reapply_text.index("purified, purification = purify_bytes(patched)") < reapply_text.index(
        "digest = hashlib.sha256(patched).hexdigest()"
    ), "Terser purification must precede content-addressing"

    # Purification itself is exact-version, non-mangling and fixed-point aware.
    for required in (
        'TERSER_VERSION = "5.50.0"',
        "def _stable_candidate(",
        "_run_purifier(first, format_only=format_only)",
        '"--format-only"',
        '"fixedPointVerified": fixed_point_verified',
        "validate_provider_artifact.cjs",
    ):
        assert required in purification_text, f"missing purification contract: {required}"
    for required in (
        'EXPECTED_TERSER_VERSION = "5.50.0"',
        "mangle: false",
        "unsafe: false",
        "keep_fnames: true",
        "keep_classnames: true",
    ):
        assert required in purifier_text, f"missing Terser policy: {required}"

    # Runtime policy tests prove the complete discovery transform is byte-stable;
    # the purification contract separately proves final-Terser ordering.
    for required in (
        "assert reapplied == patched",
        'reapplied_text.count("NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1") == 1',
        'reapplied_text.count("NUVIO_GLOBAL_STREAM_PRESENTATION_V1") == 1',
        "Runtime repair phase must not inject discovery wrappers",
    ):
        assert required in playback_test, f"missing playback fixed-point test: {required}"
    for required in (
        "purified, purification = purify_bytes(patched)",
        "digest = hashlib.sha256(patched).hexdigest()",
        'EXPECTED_TERSER_VERSION = "5.50.0"',
    ):
        assert required in purification_test, f"missing purification regression test: {required}"


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.parse_args()

    assert_contract()
    print(
        "FIELD_CORE_FIXED_POINT_CONTRACT "
        "changed=0 side_effect_free=1 security_boundary=observable "
        "runtime_domain_position=stable final_terser=5.50.0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
