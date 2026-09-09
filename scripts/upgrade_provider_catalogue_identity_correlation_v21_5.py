#!/usr/bin/env python3
"""V21.5: keep provider catalogue identity scoped to the matched result.

V20.5 correctly scores provider-native catalogue paths against title/season, but
its final HTML fallback can still replace that strongly correlated id with the
most frequent generic id found anywhere in the response. On multi-result search
pages this can bind the requested title to a neighbouring card's id.

V21.5 preserves the title/season-correlated id/slug as authoritative. A global
query/data-id frequency candidate remains available only when the correlated
selector found no id at all. This is provider-agnostic and keeps the existing
proof/dataflow requirements unchanged.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import upgrade_provider_episode_scoped_json_v21_4 as v214  # noqa: E402

BASE = v214.BASE
MARKER = "NIAKVIO_PROVIDER_CATALOGUE_IDENTITY_CORRELATION_V21_5"

patch_worker = v214.patch_worker
patch_proof = v214.patch_proof
patch_recovery = v214.patch_recovery
patch_materializer = v214.patch_materializer
validate_worker = v214.validate_worker
validate_proof = v214.validate_proof
validate_recovery = v214.validate_recovery
validate_materializer = v214.validate_materializer


def _strict_span(text: str) -> tuple[int, int]:
    start = text.index("function _spv205StrictProviderValues(value, base, meta, season) {")
    end = text.index("function _spv205HttpValues", start)
    return start, end


def patch_base() -> bool:
    v214.patch_base()
    text = BASE.read_text(encoding="utf-8")
    start, end = _strict_span(text)
    strict = text[start:end]
    if MARKER in strict:
        validate_base(text)
        return False

    old = "  if (bestId) best.id = bestId;\n  return best;\n}\n"
    new = (
        "  /* " + MARKER + " */\n"
        "  // A response-wide id is fallback evidence only. Never overwrite an id\n"
        "  // that was selected from the same title/season-correlated catalogue row.\n"
        "  if (!best.id && bestId) best.id = bestId;\n"
        "  return best;\n}\n"
    )
    count = strict.count(old)
    if count != 1:
        raise AssertionError(f"v21.5 strict-id fallback anchor: expected one, got {count}")
    strict = strict.replace(old, new, 1)
    text = text[:start] + strict + text[end:]
    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return True


def validate_base(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    v214.validate_base(value)
    start, end = _strict_span(value)
    strict = value[start:end]
    for needle in (
        MARKER,
        "if (!best.id && bestId) best.id = bestId;",
        "const pathRe =",
        "const score = _spv4TitleScore(label, meta) + _spv205SeasonSignal(segment, season);",
        "const dataIdRe =",
    ):
        if needle not in strict:
            raise AssertionError(f"V21.5 strict catalogue selector missing {needle}")
    if "if (bestId) best.id = bestId;" in strict:
        raise AssertionError("V21.5 still allows response-wide id to overwrite correlated id")
    lowered = strict.casefold()
    for forbidden in (
        "french-manga",
        "jujutsu",
        "animevostfr",
        "animesama",
        "vidzy",
        "purstream",
        "1497198",
        "1497822",
    ):
        if forbidden in lowered:
            raise AssertionError(f"V21.5 provider/fixture-specific token leaked: {forbidden}")


def main() -> int:
    changed = patch_worker() | patch_proof() | patch_recovery() | patch_materializer() | patch_base()
    validate_worker()
    validate_proof()
    validate_recovery()
    validate_materializer()
    validate_base()
    print(
        f"PROVIDER_CATALOGUE_IDENTITY_CORRELATION_V21_5_OK changed={str(changed).lower()} "
        "matched_row_id_authoritative=1 global_id_fallback_only=1 "
        "title_season_scoring_preserved=1 proof_dataflow_preserved=1 "
        "provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
