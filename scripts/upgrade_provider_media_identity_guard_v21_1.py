#!/usr/bin/env python3
"""V21.1: media-aware provider identity selection and tracking-id rejection.

The provider-value resolver must not collapse franchise proximity into identity.
For series/anime requests, a catalogue candidate that is only the exact requested
series title plus a bare numeric installment (for example a prequel film "... 0")
is not the requested series unless that full title is itself a TMDB alias.
For movie requests, a conflicting explicit year is a hard rejection while series
season/episode markers cannot beat a non-exact movie identity.

The same layer also rejects analytics/tracking identifiers from providerId
extraction. No provider names, hosts, fixture titles or provider-specific ids are
encoded in executable runtime logic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import upgrade_provider_shared_player_trace_v21 as v21  # noqa: E402

BASE = v21.BASE
MARKER = "NIAKVIO_PROVIDER_MEDIA_IDENTITY_GUARD_V21_1"

patch_worker = v21.patch_worker
patch_proof = v21.patch_proof
patch_recovery = v21.patch_recovery
patch_materializer = v21.patch_materializer
validate_worker = v21.validate_worker
validate_proof = v21.validate_proof
validate_recovery = v21.validate_recovery
validate_materializer = v21.validate_materializer


def _once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_base() -> bool:
    v21.patch_base()
    text = BASE.read_text(encoding="utf-8")
    if MARKER in text:
        validate_base(text)
        return False

    anchor = "function _spv205StrictProviderValues(value, base, meta, season) {\n"
    helper = r'''/* NIAKVIO_PROVIDER_MEDIA_IDENTITY_GUARD_V21_1 */
function _spv211RegexEscape(value) {
  return _text(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
function _spv211CandidateIdentityScore(title, href, meta, mediaType, season) {
  const actual = _slug(title);
  if (!actual) return 0;
  const expected = _spv4Titles(meta).map(_slug).filter(Boolean);
  const exact = expected.includes(actual);
  let score = _spv4TitleScore(title, meta);
  const lane = _text(mediaType).toLowerCase();
  const context = _text(title) + " " + _text(href);

  if (lane === "movie") {
    if (!exact && /(?:^|[\s/_-])(?:saison|season|episode|ep)[\s._-]*\d{1,3}\b/i.test(context)) return -10000;
    const wantedYear = Number(meta && (meta.year || meta.releaseYear || meta.release_year));
    const years = context.match(/\b(?:19|20)\d{2}\b/g) || [];
    if (Number.isFinite(wantedYear) && wantedYear > 1800 && years.length) {
      if (!years.some(value => Number(value) === wantedYear)) return -10000;
      score += 100;
    }
    return score;
  }

  // Anime is a TV-series identity lane at the TMDB boundary. A non-exact bare
  // numeric franchise installment is not a season signal and commonly denotes
  // another work (movie/prequel/sequel). Accept it only when TMDB itself exposes
  // that complete title as an alias, which is covered by exact=true above.
  if (!exact) {
    for (const wanted of expected) {
      const suffix = actual.match(new RegExp("^" + _spv211RegexEscape(wanted) + "-(\\d{1,3})$", "i"));
      if (suffix) return -10000;
    }
  }
  score += _spv205SeasonSignal(context, season);
  return score;
}
function _spv211ProviderIdAllowed(key, rawValue) {
  const field = _text(key).trim().toLowerCase();
  const value = _text(rawValue).trim();
  if (!value || value.length > 160) return false;
  if (/tracking|analytics|measurement|gtag|google[_-]?tag|pixel|telemetry|client[_-]?id|visitor[_-]?id/i.test(field)) return false;
  if (/^(?:G-[A-Z0-9]{6,}|GTM-[A-Z0-9-]{4,}|UA-\d+(?:-\d+)?|AW-\d+)$/i.test(value)) return false;
  return /^[A-Za-z0-9._~-]{1,160}$/.test(value);
}
'''
    text = _once(
        text,
        anchor,
        helper + "function _spv205StrictProviderValues(value, base, meta, season, mediaType) {\n",
        "v21.1-helper-and-signature",
    )

    # V20.4 intentionally still owns an older response-value helper with some
    # similar data-id patterns. Patch only the current V20.5 strict resolver so
    # historical ownership remains byte-stable and the migration has one owner.
    strict_start = text.index("function _spv205StrictProviderValues(value, base, meta, season, mediaType) {")
    strict_end = text.index("\nfunction _spv205HttpValues(", strict_start)
    strict = text[strict_start:strict_end]

    old_json_score = '''        score: _spv4TitleScore(
          _spv4Scalar(row.title) || _spv4Scalar(row.name) ||
          _spv4Scalar(row.original_title) || _spv4Scalar(row.post_title) ||
          _spv4Scalar(row.label) || "",
          meta
        )
'''
    new_json_score = '''        score: _spv211CandidateIdentityScore(
          _spv4Scalar(row.title) || _spv4Scalar(row.name) ||
          _spv4Scalar(row.original_title) || _spv4Scalar(row.post_title) ||
          _spv4Scalar(row.label) || "",
          _spv4Scalar(row.url) || _spv4Scalar(row.href) || _spv4Scalar(row.permalink) || "",
          meta,
          mediaType,
          season
        )
'''
    strict = _once(strict, old_json_score, new_json_score, "v21.1-json-media-score")

    strict = _once(
        strict,
        '    const score = _spv4TitleScore(label, meta) + _spv205SeasonSignal(label + " " + href, season);\n',
        '    const score = _spv211CandidateIdentityScore(label, href, meta, mediaType, season);\n',
        "v21.1-html-media-score",
    )
    strict = _once(
        strict,
        '    const score = _spv4TitleScore(label, meta) + _spv205SeasonSignal(segment, season);\n',
        '    const score = _spv211CandidateIdentityScore(label, segment, meta, mediaType, season);\n',
        "v21.1-path-media-score",
    )

    strict = _once(
        strict,
        '''    const idMatch = attrs.match(/\\bdata-(?:id|post-id|media-id|anime-id|movie-id|series-id|show-id)\\s*=\\s*["']?([A-Za-z0-9._~-]{1,160})/i);
    if (idMatch) id = idMatch[1];
''',
        '''    const idMatch = attrs.match(/\\bdata-(id|post-id|media-id|anime-id|movie-id|series-id|show-id)\\s*=\\s*["']?([A-Za-z0-9._~-]{1,160})/i);
    if (idMatch && _spv211ProviderIdAllowed(idMatch[1], idMatch[2])) id = idMatch[2];
''',
        "v21.1-anchor-id-filter",
    )
    strict = _once(
        strict,
        '''      if (!/(?:^|[_-])id$|id$/i.test(key)) continue;
      if (!/^[A-Za-z0-9._~-]{1,160}$/.test(candidate)) continue;
      const count = (counts.get(candidate) || 0) + 1;
''',
        '''      if (!/(?:^|[_-])id$|id$/i.test(key)) continue;
      if (!_spv211ProviderIdAllowed(key, candidate)) continue;
      const count = (counts.get(candidate) || 0) + 1;
''',
        "v21.1-query-id-filter",
    )
    strict = _once(
        strict,
        '''  const dataIdRe = /\\bdata-(?:id|[a-z0-9_-]*[_-]id)\\s*=\\s*["']?([A-Za-z0-9._~-]{1,160})/gi;
  scanned = 0;
  while ((match = dataIdRe.exec(source)) !== null && scanned++ < 320) {
    const candidate = _text(match[1]).trim();
    if (!candidate) continue;
    const count = (counts.get(candidate) || 0) + 1;
''',
        '''  const dataIdRe = /\\bdata-((?:id|[a-z0-9_-]*[_-]id))\\s*=\\s*["']?([A-Za-z0-9._~-]{1,160})/gi;
  scanned = 0;
  while ((match = dataIdRe.exec(source)) !== null && scanned++ < 320) {
    const key = _text(match[1]).trim();
    const candidate = _text(match[2]).trim();
    if (!_spv211ProviderIdAllowed(key, candidate)) continue;
    const count = (counts.get(candidate) || 0) + 1;
''',
        "v21.1-generic-data-id-filter",
    )
    text = text[:strict_start] + strict + text[strict_end:]

    # Both initial search identity and step-response identity must know the
    # requested semantic media lane.
    text = _once(
        text,
        '''        meta,
        season
      ) || { id: "", slug: "" };
''',
        '''        meta,
        season,
        mediaType
      ) || { id: "", slug: "" };
''',
        "v21.1-search-media-type",
    )
    text = _once(
        text,
        '''            meta,
            season
          ) || { id: "", slug: "" };
''',
        '''            meta,
            season,
            mediaType
          ) || { id: "", slug: "" };
''',
        "v21.1-step-media-type",
    )

    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return True


def validate_base(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    v21.validate_base(value)
    for needle in (
        MARKER,
        "function _spv211CandidateIdentityScore",
        "function _spv211ProviderIdAllowed",
        "function _spv205StrictProviderValues(value, base, meta, season, mediaType)",
        "score: _spv211CandidateIdentityScore(",
        "const score = _spv211CandidateIdentityScore(label, href, meta, mediaType, season);",
        "if (!_spv211ProviderIdAllowed(key, candidate)) continue;",
        "season,\n        mediaType",
        "season,\n            mediaType",
    ):
        if needle not in value:
            raise AssertionError(f"V21.1 ProviderBase missing {needle}")
    runtime = value[value.index(MARKER): value.index("async function _resolveSearchRequestPlan", value.index(MARKER))]
    lowered = runtime.casefold()
    for forbidden in ("jujutsu", "animesama", "animevostfr", "french-manga", "purstream"):
        if forbidden in lowered:
            raise AssertionError(f"V21.1 provider/fixture-specific token leaked: {forbidden}")


def main() -> int:
    changed = patch_worker() | patch_proof() | patch_recovery() | patch_materializer() | patch_base()
    validate_worker()
    validate_proof()
    validate_recovery()
    validate_materializer()
    validate_base()
    print(
        f"PROVIDER_MEDIA_IDENTITY_GUARD_V21_1_OK changed={str(changed).lower()} "
        "media_type_aware=1 series_numeric_installment_reject=1 movie_year_strict=1 "
        "tracking_provider_ids_rejected=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
