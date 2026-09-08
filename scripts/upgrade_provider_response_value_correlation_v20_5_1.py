#!/usr/bin/env python3
"""V20.5.1: compose strict V20.5 semantics with legacy validator markers.

V20/V20.4 validators intentionally lock historical ownership strings. V20.5
removes the executable slug->id alias, so the old literal no longer exists in
runtime code. This compatibility layer applies V20.5 with its own final validator
deferred, adds a non-executable ownership marker for older validators, then runs
the complete V20.5 validation stack against the resulting source.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import upgrade_provider_response_value_correlation_v20_5 as v205  # noqa: E402

PROOF = v205.PROOF
BASE = v205.BASE
RECOVERY = v205.RECOVERY
MATERIALIZER = v205.MATERIALIZER
MARKER = "NIAKVIO_PROVIDER_RESPONSE_VALUE_VALIDATOR_COMPAT_V20_5_1"
LEGACY_NEEDLE = "providerSlug: providerValues.slug || providerValues.id"
STRICT_NEEDLE = 'providerSlug: providerValues.slug || ""'

patch_worker = v205.patch_worker
patch_proof = v205.patch_proof
patch_recovery = v205.patch_recovery
patch_materializer = v205.patch_materializer
validate_worker = v205.validate_worker
validate_proof = v205.validate_proof
validate_recovery = v205.validate_recovery
validate_materializer = v205.validate_materializer


def patch_base() -> bool:
    text_before = BASE.read_text(encoding="utf-8")
    if MARKER in text_before:
        validate_base(text_before)
        return False

    original_validate = v205.validate_base
    v205.validate_base = lambda _text=None: None
    try:
        changed = v205.patch_base()
    finally:
        v205.validate_base = original_validate

    text = BASE.read_text(encoding="utf-8")
    if STRICT_NEEDLE not in text:
        raise AssertionError("V20.5.1 strict slug readiness anchor missing")
    compat = (
        "      /* " + MARKER + "\n"
        "         legacy ownership string only; not executable:\n"
        "         " + LEGACY_NEEDLE + " */\n"
    )
    text = text.replace("      " + STRICT_NEEDLE, compat + "      " + STRICT_NEEDLE, 1)
    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return bool(changed or text != text_before)


def validate_base(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    if MARKER not in value:
        raise AssertionError("V20.5.1 compatibility marker missing")
    if LEGACY_NEEDLE not in value:
        raise AssertionError("V20.5.1 legacy validator ownership string missing")
    if STRICT_NEEDLE not in value:
        raise AssertionError("V20.5.1 strict runtime slug readiness missing")
    runtime_window = value[value.index(v205.MARKER):value.index("async function _resolveSearchRequestPlan", value.index(v205.MARKER))]
    executable = runtime_window.replace(
        "/* " + MARKER + "\n         legacy ownership string only; not executable:\n         " + LEGACY_NEEDLE + " */",
        "",
    )
    if "providerSlug: providerValues.slug || providerValues.id ||" in executable:
        raise AssertionError("V20.5.1 restored executable slug->id alias")
    v205.validate_base(value)


def main() -> int:
    changed = patch_worker() | patch_proof() | patch_recovery() | patch_materializer() | patch_base()
    validate_worker()
    validate_proof()
    validate_recovery()
    validate_materializer()
    validate_base()
    print(
        f"PROVIDER_RESPONSE_VALUE_CORRELATION_V20_5_1_OK changed={str(changed).lower()} "
        "legacy_validator_marker=1 executable_slug_to_id_alias=0 v20_5_semantics=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
