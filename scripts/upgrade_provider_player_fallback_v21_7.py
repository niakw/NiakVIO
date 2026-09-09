#!/usr/bin/env python3
"""V21.7: carry exact proof-correlated player fallback provenance to the terminal sanitizer.

V21.6 deliberately preserves a failed player/embed URL as a native-player fallback
only after a live proof-correlated provider-value plan reaches that exact step.
The terminal all-URL sanitizer must be able to distinguish this narrow fallback
from an arbitrary unverified URL. V21.7 adds a private, exact-URL marker to those
rows; the terminal sanitizer consumes and strips it before publication.

No provider id, host, fixture, token, credential or media URL is embedded here.
Direct media is never marked by this contract.
"""
from __future__ import annotations

from pathlib import Path

import upgrade_provider_player_fallback_v21_6 as v216

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_PLAYER_FALLBACK_V21_7"
PRIVATE_FIELD = "__nuvioCorrelatedPlayerFallbackV1"

# Keep all earlier owners chained through the canonical V21.6 entry points.
patch_worker = v216.patch_worker
patch_proof = v216.patch_proof
patch_recovery = v216.patch_recovery
patch_materializer = v216.patch_materializer
validate_worker = v216.validate_worker
validate_proof = v216.validate_proof
validate_recovery = v216.validate_recovery
validate_materializer = v216.validate_materializer


def patch_base() -> bool:
    v216.patch_base()
    text = BASE.read_text(encoding="utf-8")
    if MARKER in text:
        validate_base(text)
        return False

    old = '''    out.push(..._streams([url], _text(row && row.referer)));
'''
    new = '''    const emitted = _streams([url], _text(row && row.referer));
    for (const stream of emitted) {
      if (stream && typeof stream === "object") {
        stream.__nuvioCorrelatedPlayerFallbackV1 = { url };
      }
      out.push(stream);
    }
'''
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"V21.7 fallback emission anchor count={count}")
    text = text.replace(old, new, 1)

    anchor = "function _spv216FallbackStreams(rows) {\n"
    if text.count(anchor) != 1:
        raise AssertionError("V21.7 V21.6 helper anchor missing")
    text = text.replace(anchor, f"/* {MARKER} */\n" + anchor, 1)
    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return True


def validate_base(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    if value.count(MARKER) != 1:
        raise AssertionError(f"V21.7 marker count={value.count(MARKER)}")
    for needle in (
        "function _spv216FallbackStreams(rows)",
        "const emitted = _streams([url], _text(row && row.referer));",
        "stream.__nuvioCorrelatedPlayerFallbackV1 = { url };",
        "if (!_spv216PlayerFallbackEligible(url)) continue;",
    ):
        if needle not in value:
            raise AssertionError(f"V21.7 missing {needle}")
    section = value.split(f"/* {MARKER} */", 1)[1].split("async function _resolveProviderValuePlan", 1)[0].casefold()
    for forbidden in (
        "animesama",
        "animevostfr",
        "french-manga",
        "jujutsu",
        "4668025",
        "1497198",
    ):
        if forbidden in section:
            raise AssertionError(f"V21.7 provider-specific token leaked: {forbidden}")


def main() -> int:
    patch_worker(); patch_proof(); patch_recovery(); patch_materializer()
    changed = patch_base()
    validate_worker(); validate_proof(); validate_recovery(); validate_materializer(); validate_base()
    print(
        f"PROVIDER_PLAYER_FALLBACK_V21_7_OK changed={str(changed).lower()} "
        "exact_correlated_marker=1 direct_media_marked=0 private_marker=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
