#!/usr/bin/env python3
"""V21.12: close generic reconstruction gaps exposed by live Repair V6 proof.

Three shared failures remained after V21.11:
- an explicitly different season could still win catalogue identity scoring;
- a proof-correlated player/embed that returned HTTP 2xx was discarded when the
  bounded crawler could not resolve it to direct media;
- identity-keyed catalogue searches ({imdbId}/{tmdbId}) were not recognised as
  search authority, preventing their correlated provider-value chains from being
  materialized even when the same live trace produced streams.

V21.12 is deliberately provider-agnostic. It does not add hosts, provider ids,
fixture titles, media URLs or volatile response values. Explicit season mismatch
fails closed; only already proof-correlated non-direct player URLs can become the
existing private player fallback; and identity search keys are runtime-owned TMDB
metadata already present in the request contract. Identity-keyed routes are only
classified as catalogue search when the live trace itself marks role=search, so
typed resolver APIs retain their earlier V7 authority.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "provider_base_store.py"
RECOVERY = ROOT / "scripts" / "recover_provider_routes_from_upstreams.py"
MARKER = "NIAKVIO_PROVIDER_RUNTIME_RECONSTRUCTION_V21_12"
RECOVERY_MARKER = "ROUTE_RECOVERY_IDENTITY_SEARCH_V21_12"


def _once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_recovery() -> bool:
    text = RECOVERY.read_text(encoding="utf-8")
    if RECOVERY_MARKER in text:
        validate_recovery(text)
        return False
    if "ROUTE_RECOVERY_COMPOSITE_SEARCH_TEMPLATE_V21_8" not in text:
        raise AssertionError("V21.12 requires V21.8 composite search recovery")

    start = text.index("def _record_has_search_query(row: dict[str, Any]) -> bool:\n")
    end = text.index("\ndef ", start + 5)
    section = text[start:end]
    expected = '''def _record_has_search_query(row: dict[str, Any]) -> bool:
    route = str(row.get("route") or "")
    if any(marker in route for marker in ("{query}", "{queryDots}", "{query_dots}")):
        return True
    spec = request_spec(row)
    if not isinstance(spec, dict):
        return False
    # Request specs are already sanitized/abstracted proof DATA. Searching the
    # serialized structure here only detects the canonical placeholder produced
    # by proof abstraction; it never recovers arbitrary provider code/data.
    serialized = json.dumps(spec, ensure_ascii=False, sort_keys=True)
    return any(marker in serialized for marker in ("{query}", "{queryDots}", "{query_dots}"))
'''
    if section.strip() != expected.strip():
        raise AssertionError("V21.12 recovery search classifier anchor drifted")
    replacement = '''# ROUTE_RECOVERY_IDENTITY_SEARCH_V21_12
def _record_has_search_query(row: dict[str, Any]) -> bool:
    route = str(row.get("route") or "")
    query_markers = ("{query}", "{queryDots}", "{query_dots}")
    identity_markers = ("{imdbId}", "{imdb_id}", "{tmdbId}", "{tmdb_id}")
    if any(marker in route for marker in query_markers):
        return True
    role = str(row.get("role") or "").strip().casefold()
    if role == "search" and any(marker in route for marker in identity_markers):
        return True
    spec = request_spec(row)
    if not isinstance(spec, dict):
        return False
    # Request specs are already sanitized/abstracted proof DATA. Searching the
    # serialized structure here only detects canonical proof placeholders.
    serialized = json.dumps(spec, ensure_ascii=False, sort_keys=True)
    return any(marker in serialized for marker in query_markers) or (
        role == "search" and any(marker in serialized for marker in identity_markers)
    )
'''
    text = text[:start] + replacement + text[end:]
    RECOVERY.write_text(text, encoding="utf-8")
    validate_recovery(text)
    return True


def patch_base() -> bool:
    text = BASE.read_text(encoding="utf-8")
    if MARKER in text:
        validate_base(text)
        return False
    for required in (
        "NIAKVIO_PROVIDER_MEDIA_IDENTITY_GUARD_V21_1",
        "NIAKVIO_PROVIDER_PLAYER_FALLBACK_V21_7",
    ):
        if required not in text:
            raise AssertionError(f"V21.12 requires {required}")

    old_season = '''  score += _spv205SeasonSignal(context, season);
  return score;
}'''
    new_season = '''  /* NIAKVIO_PROVIDER_RUNTIME_RECONSTRUCTION_V21_12 */
  const explicitSeasonSignal = _spv205SeasonSignal(context, season);
  if (explicitSeasonSignal < 0) return -10000;
  score += explicitSeasonSignal;
  return score;
}'''
    text = _once(text, old_season, new_season, "v21.12-explicit-season-fail-closed")

    old_crawl = '''        if (crawl.length) {
          const streams = await _crawlDirectMedia(crawl.slice(0, 10), payload.base || stepUrl, 3);
          if (streams.length) return streams.slice(0, 40);
        }
'''
    new_crawl = '''        if (crawl.length) {
          const streams = await _crawlDirectMedia(crawl.slice(0, 10), payload.base || stepUrl, 3);
          if (streams.length) return streams.slice(0, 40);
          // V21.12: a successful HTTP player page is still a valid native-player
          // fallback when this exact URL came from the proof-correlated response.
          // Direct media remains on the ordinary probed path and is never marked.
          const fallbackReferer = _text(payload.base || stepUrl);
          for (const candidate of crawl.slice(0, 10)) {
            if (_directMedia(candidate) || !_spv216PlayerFallbackEligible(candidate)) continue;
            if (!playerFallbacks.some(row => row.url === candidate)) {
              playerFallbacks.push({ url: candidate, referer: fallbackReferer });
            }
          }
        }
'''
    text = _once(text, old_crawl, new_crawl, "v21.12-successful-player-fallback")

    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return True


def validate_recovery(text: str | None = None) -> None:
    value = text if text is not None else RECOVERY.read_text(encoding="utf-8")
    if value.count(RECOVERY_MARKER) != 1:
        raise AssertionError(f"V21.12 recovery marker count={value.count(RECOVERY_MARKER)}")
    start = value.index("def _record_has_search_query(row: dict[str, Any]) -> bool:\n")
    end = value.index("\ndef ", start + 5)
    section = value[start:end]
    for needle in (
        'query_markers = ("{query}", "{queryDots}", "{query_dots}")',
        'identity_markers = ("{imdbId}", "{imdb_id}", "{tmdbId}", "{tmdb_id}")',
        'role == "search" and any(marker in route for marker in identity_markers)',
        'return any(marker in serialized for marker in query_markers) or (',
    ):
        if needle not in section:
            raise AssertionError(f"V21.12 recovery missing {needle}")


def validate_base(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    if value.count(MARKER) != 1:
        raise AssertionError(f"V21.12 base marker count={value.count(MARKER)}")
    for needle in (
        "const explicitSeasonSignal = _spv205SeasonSignal(context, season);",
        "if (explicitSeasonSignal < 0) return -10000;",
        "if (_directMedia(candidate) || !_spv216PlayerFallbackEligible(candidate)) continue;",
        "playerFallbacks.push({ url: candidate, referer: fallbackReferer });",
    ):
        if needle not in value:
            raise AssertionError(f"V21.12 ProviderBase missing {needle}")
    start = value.index(MARKER)
    end = value.index("async function _resolveSearchRequestPlan", start)
    section = value[start:end].casefold()
    for forbidden in (
        "animevostfr",
        "mugiwarastream",
        "vegamovies",
        "jujutsu",
        "smoothpre",
        "cineby",
    ):
        if forbidden in section:
            raise AssertionError(f"V21.12 provider/fixture-specific token leaked: {forbidden}")


def main() -> int:
    recovery_changed = patch_recovery()
    base_changed = patch_base()
    validate_recovery(); validate_base()
    changed = recovery_changed or base_changed
    print(
        f"PROVIDER_RUNTIME_RECONSTRUCTION_V21_12_OK changed={str(changed).lower()} "
        "explicit_season_mismatch_fail_closed=1 successful_correlated_player_fallback=1 "
        "identity_keyed_search_role_gated=1 typed_resolver_api_preserved=1 "
        "direct_media_fallback_bypass=0 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
