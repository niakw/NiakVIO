#!/usr/bin/env python3
"""V21.9: preserve strict JSON provider values before catalogue fallback.

A provider-value search response can be JSON serialized as text. The V21.5
catalogue pass was applied unconditionally after the JSON parse and could erase a
valid slug/id pair because it treated that same JSON text as HTML. That leaves
proof-backed {slug} steps permanently deferred even though the upstream search
returned the exact slug.

V21.9 keeps opaque provider id and catalogue slug distinct. It extracts explicit
JSON id fields and explicit JSON slug fields separately, then lets the catalogue
HTML parser augment missing values only; it never overwrites a value already
proved by the strict JSON parse. No provider-specific token or route is encoded.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_JSON_CATALOGUE_PRESERVATION_V21_9"


def _once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_base() -> bool:
    text = BASE.read_text(encoding="utf-8")
    if MARKER in text:
        changed = False
        stale_to_current = (
            (
                'id: catalogueProviderValues.id || providerValues.id || ""',
                'id: providerValues.id || catalogueProviderValues.id || ""',
            ),
            (
                'slug: catalogueProviderValues.slug || providerValues.slug || ""',
                'slug: providerValues.slug || catalogueProviderValues.slug || ""',
            ),
        )
        for stale, current in stale_to_current:
            if stale in text:
                text = _once(text, stale, current, "v21.9-stale-marked-precedence")
                changed = True
        if changed:
            BASE.write_text(text, encoding="utf-8")
        validate_base(text)
        return changed

    helper_anchor = "function _spv215CatalogueProviderValues(value, base, meta, season, mediaType) {\n"
    helper = r'''/* NIAKVIO_PROVIDER_JSON_CATALOGUE_PRESERVATION_V21_9 */
function _spv219JsonProviderValues(value, meta, season, mediaType) {
  const rows = _spv4JsonRows(value, []).slice(0, 300);
  const idKeys = ["id","ID","_id","media_id","post_id","anime_id","movie_id","series_id","show_id"];
  const slugKeys = ["slug","provider_slug","seo_slug"];
  let best = { id: "", slug: "", score: -1e9 };
  for (const row of rows) {
    if (!row || typeof row !== "object") continue;
    const label =
      _spv4Scalar(row.title) || _spv4Scalar(row.name) ||
      _spv4Scalar(row.original_title) || _spv4Scalar(row.post_title) ||
      _spv4Scalar(row.label) || _spv4Scalar(row.anime) ||
      _spv4Scalar(row.movie) || _spv4Scalar(row.series) ||
      _spv4Scalar(row.show) || _spv4Scalar(row.matched) || "";
    const href = _spv4Scalar(row.url) || _spv4Scalar(row.href) || _spv4Scalar(row.permalink) || "";
    const score = _spv211CandidateIdentityScore(label, href, meta, mediaType, season);
    if (score < 90 || score < best.score) continue;
    let id = "";
    let slug = "";
    for (const key of idKeys) {
      const candidate = _spv4Scalar(row[key]);
      if (_spv211ProviderIdAllowed(key, candidate)) { id = candidate; break; }
    }
    for (const key of slugKeys) {
      const candidate = _spv4Scalar(row[key]);
      if (candidate && candidate.length <= 160 && /^[A-Za-z0-9._~-]+$/.test(candidate)) { slug = candidate; break; }
    }
    if (!id && !slug) continue;
    if (score > best.score) best = { id, slug, score };
  }
  return { id: best.id || "", slug: best.slug || "" };
}
'''
    text = _once(text, helper_anchor, helper + helper_anchor, "v21.9-json-helper")

    old = r'''      let providerValues = { id: "", slug: "" };
      if (typeof searchPayload.value === "string") {
        const rawSearchValue = _text(searchPayload.value).trim();
        if (rawSearchValue && rawSearchValue.length <= 4 * 1024 * 1024 && /^[\[{]/.test(rawSearchValue)) {
          try {
            providerValues = _spv20ProviderValuesFromJson(JSON.parse(rawSearchValue), meta);
          } catch (_) {}
        }
        if (!providerValues || (!providerValues.id && !providerValues.slug)) {
          providerValues = _spv20ProviderValuesFromHtml(rawSearchValue, meta);
        }
      } else {
        providerValues = _spv20ProviderValuesFromJson(searchPayload.value, meta);
      }
      providerValues = _spv215CatalogueProviderValues(
        searchPayload.value,
        searchPayload.base || searchUrl,
        meta,
        season,
        mediaType
      ) || { id: "", slug: "" };
'''
    new = r'''      let providerValues = { id: "", slug: "" };
      if (typeof searchPayload.value === "string") {
        const rawSearchValue = _text(searchPayload.value).trim();
        if (rawSearchValue && rawSearchValue.length <= 4 * 1024 * 1024 && /^[\[{]/.test(rawSearchValue)) {
          try {
            providerValues = _spv219JsonProviderValues(JSON.parse(rawSearchValue), meta, season, mediaType);
          } catch (_) {}
        }
        if (!providerValues || (!providerValues.id && !providerValues.slug)) {
          providerValues = _spv20ProviderValuesFromHtml(rawSearchValue, meta);
        }
      } else {
        providerValues = _spv219JsonProviderValues(searchPayload.value, meta, season, mediaType);
      }
      const catalogueProviderValues = _spv215CatalogueProviderValues(
        searchPayload.value,
        searchPayload.base || searchUrl,
        meta,
        season,
        mediaType
      ) || { id: "", slug: "" };
      providerValues = {
        id: providerValues.id || catalogueProviderValues.id || "",
        slug: providerValues.slug || catalogueProviderValues.slug || ""
      };
'''
    text = _once(text, old, new, "v21.9-json-authority-merge")
    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return True


def validate_base(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    for needle in (
        MARKER,
        "function _spv219JsonProviderValues(value, meta, season, mediaType)",
        "providerValues = _spv219JsonProviderValues(JSON.parse(rawSearchValue), meta, season, mediaType);",
        "const catalogueProviderValues = _spv215CatalogueProviderValues(",
        "id: providerValues.id || catalogueProviderValues.id || \"\"",
        "slug: providerValues.slug || catalogueProviderValues.slug || \"\"",
    ):
        if needle not in value:
            raise AssertionError(f"V21.9 ProviderBase missing {needle}")
    window = value[value.index(MARKER):value.index("async function _resolveSearchRequestPlan", value.index(MARKER))]
    lowered = window.casefold()
    for forbidden in ("mugiwara", "jujutsu", "cineby", "voiranime", "vegamovies"):
        if forbidden in lowered:
            raise AssertionError(f"V21.9 provider/fixture-specific token leaked: {forbidden}")


def main() -> int:
    changed = patch_base()
    validate_base()
    print(
        f"PROVIDER_JSON_CATALOGUE_PRESERVATION_V21_9_OK changed={str(changed).lower()} "
        "strict_json_values_preserved=1 id_slug_distinct=1 catalogue_augments_only=1 stale_marked_owner_repaired=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
