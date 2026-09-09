#!/usr/bin/env python3
"""V21.4: scope episode-indexed response JSON before extracting player URLs.

Some catalogue APIs return a whole season as nested JSON, commonly
language -> episode number -> server map. The correlated-value runtime used to
walk every HTTP value in that payload, so a TV/anime S1E1 request could crawl a
player belonging to a different episode and then inherit the requested S/E in
presentation metadata.

This migration detects structural episode tables and episode-tagged arrays,
selects only the requested episode branch, and then lets the existing generic
URL/crawler logic operate. Movie and non-episodic JSON remain unchanged. No
provider, host, fixture title or site-specific field is encoded.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import upgrade_provider_series_slug_role_v21_3 as v213  # noqa: E402

BASE = v213.BASE
MARKER = "NIAKVIO_PROVIDER_EPISODE_SCOPED_JSON_V21_4"

patch_worker = v213.patch_worker
patch_proof = v213.patch_proof
patch_recovery = v213.patch_recovery
patch_materializer = v213.patch_materializer
validate_worker = v213.validate_worker
validate_proof = v213.validate_proof
validate_recovery = v213.validate_recovery
validate_materializer = v213.validate_materializer


def _once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def _resolver_span(text: str) -> tuple[int, int]:
    start = text.index("async function _resolveProviderValuePlan(meta, mediaType, season, episode) {")
    end = text.index("async function _resolveSearchRequestPlan", start)
    return start, end


def patch_base() -> bool:
    v213.patch_base()
    text = BASE.read_text(encoding="utf-8")
    if MARKER in text:
        validate_base(text)
        return False

    anchor = "function _spv211ProviderIdAllowed(key, rawValue) {\n"
    helper = r'''/* NIAKVIO_PROVIDER_EPISODE_SCOPED_JSON_V21_4 */
function _spv214EpisodeNumber(row) {
  if (!row || typeof row !== "object" || Array.isArray(row)) return 0;
  for (const key of ["episode", "episode_number", "episodeNumber", "ep", "number", "num"]) {
    const value = Number(row[key]);
    if (Number.isFinite(value) && value > 0 && value <= 10000) return Math.floor(value);
  }
  return 0;
}
function _spv214EpisodeTableKeys(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return [];
  const keys = Object.keys(value).filter(key => /^\d{1,4}$/.test(key));
  if (!keys.length) return [];
  // Episode maps point to structured server/source rows. Numeric quality maps
  // normally point straight to strings and must not be treated as episodes.
  const structured = keys.filter(key => {
    const child = value[key];
    return !!child && typeof child === "object";
  });
  return structured.length === keys.length ? keys : [];
}
function _spv214EpisodeScopedValue(value, mediaType, episode, depth) {
  const lane = _text(mediaType).trim().toLowerCase();
  const wanted = Math.floor(Number(episode) || 0);
  depth = Number(depth) || 0;
  if ((lane !== "tv" && lane !== "anime") || wanted <= 0 || depth > 10 || value == null) return value;

  if (Array.isArray(value)) {
    const tagged = value.filter(row => _spv214EpisodeNumber(row) > 0);
    if (tagged.length) {
      const exact = tagged.filter(row => _spv214EpisodeNumber(row) === wanted);
      return exact.length ? exact : null;
    }
    return value
      .map(row => _spv214EpisodeScopedValue(row, lane, wanted, depth + 1))
      .filter(row => row != null);
  }
  if (typeof value !== "object") return value;

  const rowEpisode = _spv214EpisodeNumber(value);
  if (rowEpisode > 0 && rowEpisode !== wanted) return null;

  const episodeKeys = _spv214EpisodeTableKeys(value);
  if (episodeKeys.length) {
    const key = String(wanted);
    if (!Object.prototype.hasOwnProperty.call(value, key)) return null;
    return _spv214EpisodeScopedValue(value[key], lane, wanted, depth + 1);
  }

  const out = {};
  for (const [key, child] of Object.entries(value).slice(0, 256)) {
    const scoped = _spv214EpisodeScopedValue(child, lane, wanted, depth + 1);
    if (scoped != null) out[key] = scoped;
  }
  return out;
}
'''
    text = _once(text, anchor, helper + anchor, "v21.4-episode-json-helper")

    start, end = _resolver_span(text)
    resolver = text[start:end]
    target = "          let urls = [];\n"
    if resolver.count(target) != 1:
        raise AssertionError(f"v21.4-resolver-url-anchor: expected one anchor, got {resolver.count(target)}")
    resolver = resolver.replace(
        target,
        "          const scopedPayloadValue = _spv214EpisodeScopedValue(payload.value, mediaType, episode, 0);\n"
        "          let urls = [];\n",
        1,
    )

    # Only the URL extraction phase is scoped. Identity state extraction above
    # remains based on the full response so provider ids/slugs can still advance.
    for old, new in (
        ('typeof payload.value === "string"', 'typeof scopedPayloadValue === "string"'),
        ('_extractUrls(payload.value, payload.base)', '_extractUrls(scopedPayloadValue, payload.base)'),
        ('_jsonUrls(payload.value)', '_jsonUrls(scopedPayloadValue)'),
        ('_sourceUrls(payload.value, payload.base)', '_sourceUrls(scopedPayloadValue, payload.base)'),
        ('_spv18ValueUrls(payload.value, payload.base, [])', '_spv18ValueUrls(scopedPayloadValue, payload.base, [])'),
        ('_spv205HttpValues(payload.value, payload.base, [])', '_spv205HttpValues(scopedPayloadValue, payload.base, [])'),
    ):
        if old not in resolver:
            raise AssertionError(f"v21.4 extraction anchor missing: {old}")
        resolver = resolver.replace(old, new)

    text = text[:start] + resolver + text[end:]
    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return True


def validate_base(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    v213.validate_base(value)
    for needle in (
        MARKER,
        "function _spv214EpisodeNumber(row)",
        "function _spv214EpisodeTableKeys(value)",
        "function _spv214EpisodeScopedValue(value, mediaType, episode, depth)",
        "const scopedPayloadValue = _spv214EpisodeScopedValue(payload.value, mediaType, episode, 0);",
        "..._spv205HttpValues(scopedPayloadValue, payload.base, [])",
    ):
        if needle not in value:
            raise AssertionError(f"V21.4 ProviderBase missing {needle}")
    start, end = _resolver_span(value)
    resolver = value[start:end]
    # Full payload remains valid for response identity extraction, but every
    # generic URL-source extractor after the scoped boundary must consume the
    # episode-scoped value.
    boundary = resolver.index("const scopedPayloadValue =")
    extraction = resolver[boundary:]
    for forbidden in (
        "_extractUrls(payload.value, payload.base)",
        "_jsonUrls(payload.value)",
        "_sourceUrls(payload.value, payload.base)",
        "_spv18ValueUrls(payload.value, payload.base, [])",
        "_spv205HttpValues(payload.value, payload.base, [])",
    ):
        if forbidden in extraction:
            raise AssertionError(f"V21.4 unscoped URL extraction remains: {forbidden}")
    lowered = value[value.index(MARKER): value.index("async function _resolveSearchRequestPlan", value.index(MARKER))].casefold()
    for forbidden in ("french-manga", "vidzy", "jujutsu", "animesama", "animevostfr", "purstream"):
        if forbidden in lowered:
            raise AssertionError(f"V21.4 provider/fixture-specific token leaked: {forbidden}")


def main() -> int:
    changed = patch_worker() | patch_proof() | patch_recovery() | patch_materializer() | patch_base()
    validate_worker()
    validate_proof()
    validate_recovery()
    validate_materializer()
    validate_base()
    print(
        f"PROVIDER_EPISODE_SCOPED_JSON_V21_4_OK changed={str(changed).lower()} "
        "episode_indexed_json_scoped=1 episode_tagged_arrays_scoped=1 "
        "movie_unchanged=1 numeric_quality_maps_unchanged=1 missing_episode_fail_closed=1 "
        "provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
