#!/usr/bin/env python3
"""V21.5: scope catalogue identity to the matched search-result record.

Run 82 proved that response-wide id suppression cannot apply to every response:
later provider/player steps legitimately learn opaque ids that replace the
catalogue identity. The stricter authority therefore belongs only to the initial
catalogue search response.

The same run also proved that path-wide inference is insufficient for HTML search
results whose title and navigation URL are correlated by a result container
(e.g. a generic search/result/card element with an onclick URL). V21.5 therefore
adds bounded same-record HTML correlation for the initial catalogue response,
keeps that correlated id authoritative against unrelated response-wide ids, and
preserves historical response-wide id learning for all later step responses.

No provider names, hosts, fixtures, or provider-specific ids are encoded in the
runtime logic.
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
    start = text.index("function _spv205StrictProviderValues(")
    end = text.index("function _spv205HttpValues", start)
    return start, end


def _once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_base() -> bool:
    v214.patch_base()
    text = BASE.read_text(encoding="utf-8")
    start, end = _strict_span(text)
    strict = text[start:end]
    if MARKER in strict:
        validate_base(text)
        return False

    old_signature = "function _spv205StrictProviderValues(value, base, meta, season, mediaType) {\n"
    helper = r'''/* NIAKVIO_PROVIDER_CATALOGUE_IDENTITY_CORRELATION_V21_5 */
function _spv215CatalogueCardValues(value, base, meta, season, mediaType) {
  const source = _text(value).slice(0, 786432);
  if (!source) return { id: "", slug: "", score: -1e9 };

  // Search/result/card containers are stronger identity evidence than an
  // unrelated path or data-id elsewhere in the same response. Split by the
  // next record start rather than trying to parse nested HTML with one regex.
  const startRe = /<(?:div|article|li)\b[^>]*\bclass\s*=\s*(["'])[^"']*(?:search[-_ ]?item|search[-_ ]?result|result[-_ ]?item|catalog(?:ue)?[-_ ]?item|media[-_ ]?item|result[-_ ]?card)[^"']*\1[^>]*>/gi;
  const starts = [];
  let match, scanned = 0;
  while ((match = startRe.exec(source)) !== null && scanned++ < 160) {
    starts.push({ index: match.index, opening: match[0] });
  }
  if (!starts.length) return { id: "", slug: "", score: -1e9 };

  let best = { id: "", slug: "", score: -1e9 };
  for (let index = 0; index < starts.length; index += 1) {
    const row = starts[index];
    const nextIndex = index + 1 < starts.length ? starts[index + 1].index : source.length;
    const card = source.slice(row.index, Math.min(nextIndex, row.index + 12000));
    const opening = row.opening;

    let href = "";
    const click = opening.match(/(?:location\s*\.\s*)?href\s*=\s*['"]([^'"]{1,900})['"]/i);
    if (click) href = click[1];
    if (!href) {
      const dataHref = opening.match(/\b(?:data-href|data-url|data-link)\s*=\s*(["'])([^"']{1,900})\1/i);
      if (dataHref) href = dataHref[2];
    }
    if (!href) {
      const anchor = card.match(/<a\b[^>]*\bhref\s*=\s*(["'])([^"']{1,900})\1[^>]*>/i);
      if (anchor) href = anchor[2];
    }
    if (!href) continue;

    let label = "";
    const title = card.match(/<[^>]*\bclass\s*=\s*(["'])[^"']*(?:search[-_ ]?title|result[-_ ]?title|item[-_ ]?title|card[-_ ]?title|media[-_ ]?title)[^"']*\1[^>]*>([\s\S]{0,2400}?)<\/(?:div|span|p|h[1-6]|a)>/i);
    if (title) label = _htmlVisibleText(title[2]).replace(/\s+/g, " ").trim();
    if (!label) continue;

    const score = _spv211CandidateIdentityScore(label, href, meta, mediaType, season);
    if (score < 90 || score <= best.score) continue;

    let id = "";
    let slug = "";
    try {
      const parsed = new URL(href, base || "https://invalid.local/");
      const raw = parsed.pathname.split("/").filter(Boolean).pop() || "";
      const segment = decodeURIComponent(raw).replace(/\.html?$/i, "");
      if (/^[A-Za-z0-9._~-]{2,160}$/.test(segment)) {
        slug = segment;
        const numeric = segment.match(/^(\d{2,})[-_.]/);
        if (numeric) id = numeric[1];
      }
      if (!id) {
        for (const key of ["newsid", "postid", "post_id", "mediaid", "media_id", "id"]) {
          const candidate = _text(parsed.searchParams.get(key)).trim();
          if (_spv211ProviderIdAllowed(key, candidate)) { id = candidate; break; }
        }
      }
    } catch (_) {}
    if (!id && !slug) continue;
    best = { id, slug, score };
  }
  return best;
}
'''
    strict = _once(
        strict,
        old_signature,
        helper + "function _spv205StrictProviderValues(value, base, meta, season, mediaType, catalogueIdentity) {\n",
        "v21.5-helper-and-signature",
    )

    old_best = '''  const source = _text(value).slice(0, 786432);
  let bestScore = -1e9;
  let best = { id: "", slug: "" };
'''
    new_best = '''  const source = _text(value).slice(0, 786432);
  let bestScore = -1e9;
  let best = { id: "", slug: "" };
  if (catalogueIdentity === true) {
    const cardBest = _spv215CatalogueCardValues(source, base, meta, season, mediaType);
    if (cardBest && (cardBest.id || cardBest.slug) && cardBest.score >= 90) {
      // Same-record title + navigation correlation outranks path-only inference.
      bestScore = cardBest.score + 100;
      best = { id: cardBest.id || "", slug: cardBest.slug || "" };
    }
  }
'''
    strict = _once(strict, old_best, new_best, "v21.5-catalogue-card-seed")

    old_tail = "  if (bestId) best.id = bestId;\n  return best;\n}\n"
    new_tail = '''  // Later step responses must retain historical response-wide id learning.
  // Only the initial catalogue response protects an already correlated row id.
  if ((catalogueIdentity !== true || !best.id) && bestId) best.id = bestId;
  return best;
}
'''
    strict = _once(strict, old_tail, new_tail, "v21.5-scoped-global-id-fallback")
    text = text[:start] + strict + text[end:]

    resolver_start = text.index("async function _resolveProviderValuePlan")
    resolver_end = text.index("async function _resolveSearchRequestPlan", resolver_start)
    resolver = text[resolver_start:resolver_end]
    old_initial = '''      providerValues = _spv205StrictProviderValues(
        searchPayload.value,
        searchPayload.base || searchUrl,
        meta,
        season,
        mediaType
      ) || { id: "", slug: "" };
'''
    new_initial = '''      providerValues = _spv205StrictProviderValues(
        searchPayload.value,
        searchPayload.base || searchUrl,
        meta,
        season,
        mediaType,
        true
      ) || { id: "", slug: "" };
'''
    resolver = _once(resolver, old_initial, new_initial, "v21.5-initial-catalogue-authority")
    text = text[:resolver_start] + resolver + text[resolver_end:]

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
        "function _spv215CatalogueCardValues(value, base, meta, season, mediaType)",
        "function _spv205StrictProviderValues(value, base, meta, season, mediaType, catalogueIdentity)",
        "bestScore = cardBest.score + 100;",
        "if ((catalogueIdentity !== true || !best.id) && bestId) best.id = bestId;",
        "const score = _spv211CandidateIdentityScore(label, segment, meta, mediaType, season);",
        "const dataIdRe =",
    ):
        if needle not in strict:
            raise AssertionError(f"V21.5 strict catalogue selector missing {needle}")

    resolver_start = value.index("async function _resolveProviderValuePlan")
    resolver_end = value.index("async function _resolveSearchRequestPlan", resolver_start)
    resolver = value[resolver_start:resolver_end]
    if "searchPayload.base || searchUrl,\n        meta,\n        season,\n        mediaType,\n        true" not in resolver:
        raise AssertionError("V21.5 initial catalogue call is not explicitly scoped")
    if "payload.base || stepUrl,\n            meta,\n            season,\n            mediaType,\n            true" in resolver:
        raise AssertionError("V21.5 incorrectly scopes later step responses as catalogue identity")

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
        "initial_catalogue_only=1 matched_record_id_authoritative=1 "
        "later_response_id_learning_preserved=1 onclick_card_correlation=1 "
        "global_id_fallback_preserved=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
