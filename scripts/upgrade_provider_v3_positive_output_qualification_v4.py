#!/usr/bin/env python3
"""V4: positive-only Provider v3 lane qualification.

A reusable type route returning HTTP 2xx/3xx is chain evidence, not proof that the
provider actually serves the requested media lane. Qualification now requires a
``playable_verified`` result for every declared semantic type in addition to the
existing route/direct-output and HTTP contracts.

This is provider-agnostic and deliberately does not special-case runner-blocked
providers: browser/device-positive evidence belongs to Native Labs, while this
reconstruction gate only credits what the current run actually proves.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "reconstruct_provider_v3_sequential_live.py"
MARKER = "PROVIDER_V3_POSITIVE_OUTPUT_QUALIFICATION_V4"

OLD = '''def is_qualified(evaluation: dict[str, Any]) -> bool:\n    \"\"\"All declared types need live evidence; HTTP success or direct output is mandatory.\"\"\"\n    if not should_pass(evaluation):\n        return False\n    if evaluation.get(\"directOutputOnly\"):\n        return True\n    return evaluation.get(\"providerSuccessHttp\") is True\n'''

NEW = '''# PROVIDER_V3_POSITIVE_OUTPUT_QUALIFICATION_V4\ndef is_qualified(evaluation: dict[str, Any]) -> bool:\n    \"\"\"Every declared lane needs current-run identity-verified playable output.\n\n    Successful route traversal is useful chain evidence, but ``no_streams`` (or\n    merely raw/unverified output) can never qualify a semantic lane by itself.\n    \"\"\"\n    if not should_pass(evaluation):\n        return False\n    required = {\n        str(value or \"\").strip().casefold()\n        for value in evaluation.get(\"requiredTypes\") or []\n        if str(value or \"\").strip()\n    }\n    playable = {\n        str(value or \"\").strip().casefold()\n        for value in evaluation.get(\"playableChainValidatedTypes\") or []\n        if str(value or \"\").strip()\n    }\n    if not required <= playable:\n        return False\n    if evaluation.get(\"directOutputOnly\"):\n        return True\n    return evaluation.get(\"providerSuccessHttp\") is True\n'''


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False
    if text.count(OLD) != 1:
        raise AssertionError(f"positive-output qualification anchor count={text.count(OLD)}")
    text = text.replace(OLD, NEW, 1)
    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    required = (
        MARKER,
        'evaluation.get("playableChainValidatedTypes")',
        "if not required <= playable:",
        'evaluation.get("providerSuccessHttp") is True',
        'evaluation.get("directOutputOnly")',
    )
    for needle in required:
        if needle not in value:
            raise AssertionError(f"positive-output V4 missing {needle}")
    window = value[value.index(MARKER): value.index(MARKER) + 1800].casefold()
    for forbidden in ("animesalt", "animepahe", "frenchstream", "vidrock", "mugiwara"):
        if forbidden in window:
            raise AssertionError(f"provider-specific qualification leaked: {forbidden}")


def main() -> int:
    changed = patch()
    print(f"PROVIDER_V3_POSITIVE_OUTPUT_QUALIFICATION_V4_OK changed={str(changed).lower()} every_lane_playable_verified=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
