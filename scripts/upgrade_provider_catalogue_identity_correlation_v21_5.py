#!/usr/bin/env python3
"""V21.5: correlate initial catalogue identity within the matched HTML record.

The historical V20.5/V21.1 strict provider-value selector is intentionally left
byte-compatible: later response steps rely on its response-wide id learning and
older migrations validate its exact media-aware signature.

V21.5 adds a separate initial-catalogue wrapper. It first evaluates the existing
strict selector as a fallback, then prefers stronger same-record HTML evidence
when a bounded search/result/card container correlates a visible title with its
own onclick/href navigation target. Only the initial search response uses this
wrapper. Later correlated steps keep calling the unchanged strict selector.

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


def _once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_base() -> bool:
    v214.patch_base()
    text = BASE.read_text(encoding="utf-8")
    if MARKER in text:
        validate_base(text)
        return False

    strict_signature = "function _spv205StrictProviderValues(value, base, meta, season, mediaType) {\n"
    helper = r'''/* NIAKVIO_PROVIDER_CATALOGUE_IDENTITY_CORRELATION_V21_5 */
function _spv215CatalogueCardValues(value, base, meta, season, mediaType) {
  const source = _text(value).slice(0, 786432);
  if (!source) return { id: "", slug: "", score: -1e9 };

  // A title and navigation target from the same search/result/card record are
  // stronger identity evidence than an unrelated path or data-id elsewhere in
  // the response. Bound both the number of records and bytes inspected.
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
function _spv215CatalogueProviderValues(value, base, meta, season, mediaType) {
  const fallback = _spv205StrictProviderValues(value, base, meta, season, mediaType) || { id: "", slug: "" };
  if (typeof value !== "string") return fallback;
  const card = _spv215CatalogueCardValues(value, base, meta, season, mediaType);
  if (!card || (!card.id && !card.slug) || card.score < 90) return fallback;
  return {
    id: card.id || fallback.id || "",
    slug: card.slug || fallback.slug || ""
  };
}
'''
    text = _once(text, strict_signature, helper + strict_signature, "v21.5-catalogue-wrapper")

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
    new_initial = '''      providerValues = _spv215CatalogueProviderValues(
        searchPayload.value,
        searchPayload.base || searchUrl,
        meta,
        season,
        mediaType
      ) || { id: "", slug: "" };
'''
    resolver = _once(resolver, old_initial, new_initial, "v21.5-initial-catalogue-wrapper-call")
    text = text[:resolver_start] + resolver + text[resolver_end:]

    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return True


def validate_base(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    v214.validate_base(value)
    for needle in (
        MARKER,
        "function _spv205StrictProviderValues(value, base, meta, season, mediaType)",
        "function _spv215CatalogueCardValues(value, base, meta, season, mediaType)",
        "function _spv215CatalogueProviderValues(value, base, meta, season, mediaType)",
        "const fallback = _spv205StrictProviderValues(value, base, meta, season, mediaType)",
        "providerValues = _spv215CatalogueProviderValues(",
    ):
        if needle not in value:
            raise AssertionError(f"V21.5 ProviderBase missing {needle}")

    resolver_start = value.index("async function _resolveProviderValuePlan")
    resolver_end = value.index("async function _resolveSearchRequestPlan", resolver_start)
    resolver = value[resolver_start:resolver_end]
    if resolver.count("providerValues = _spv215CatalogueProviderValues(") != 1:
        raise AssertionError("V21.5 catalogue wrapper must own exactly one initial identity call")
    if "const nextProviderValues = _spv215CatalogueProviderValues(" in resolver:
        raise AssertionError("V21.5 catalogue wrapper leaked into later response steps")
    if "const nextProviderValues = _spv205StrictProviderValues(" not in resolver:
        raise AssertionError("V21.5 no longer preserves historical later response id learning")

    runtime = value[value.index(MARKER):resolver_end]
    lowered = runtime.casefold()
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
        "strict_v21_1_signature_preserved=1 initial_catalogue_wrapper_only=1 "
        "matched_record_id_authoritative=1 onclick_card_correlation=1 "
        "later_response_id_learning_preserved=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
