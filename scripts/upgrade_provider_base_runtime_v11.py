#!/usr/bin/env python3
"""Execute explicitly classified typed resolver APIs without a search/base phase.

This is intentionally narrower than "absolute URL means executable". Recognition
must first classify a recipe as `typed-resolver-api`: a TMDB-addressable movie/TV
resolver whose selected provider request is terminal and already produced streams.
Multi-hop/player/search providers (VidSrc-like families included) keep their own
source plan and are never flattened by this migration.

V11 is also the single owner that chains the later V16 proof-authority ordering,
so every canonical repair runner gets the same final execution semantics.
V19 preserves a numeric TMDB routing id even when host metadata enrichment is
unavailable; enriched metadata remains optional for direct typed resolver routes.
"""
from __future__ import annotations

from pathlib import Path

import upgrade_provider_base_stream_containers_v12 as stream_v12
import upgrade_provider_execution_authority_v16 as authority_v16

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_BASE_TYPED_RESOLVER_API_V11"
RAW_TMDB_MARKER = "NIAKVIO_PROVIDER_RAW_TMDB_ROUTE_IDENTITY_V19"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def _patch_raw_tmdb_route_identity() -> bool:
    """Keep ABI TMDB route identity independent from optional metadata hydration."""
    text = TARGET.read_text(encoding="utf-8")
    if RAW_TMDB_MARKER in text:
        validate_raw_tmdb(text)
        return False

    old_meta = '''let proofMeta = null;
if (hasProofValue || hasProofRecipe || hasProofSearch) proofMeta = await _tmdb(tmdbId, type);
'''
    new_meta = '''let proofMeta = null;
if (hasProofValue || hasProofRecipe || hasProofSearch) proofMeta = await _tmdb(tmdbId, type);
/* NIAKVIO_PROVIDER_RAW_TMDB_ROUTE_IDENTITY_V19 */
const rawTmdbRouteId = _text(tmdbId).replace(/^tmdb:/i, "").split(":")[0].trim();
if (hasProofRecipe && /^\\d+$/.test(rawTmdbRouteId)) {
  if (!proofMeta) {
    proofMeta = {title:"", aliases:[], year:"", tmdbId:rawTmdbRouteId, imdbId:"", externalIds:{}};
  } else if (!_text(proofMeta.tmdbId)) {
    proofMeta = Object.assign({}, proofMeta, {tmdbId:rawTmdbRouteId});
  }
}
'''
    text = once(text, old_meta, new_meta, "raw-tmdb-route-identity")

    old_recipe = '''if (hasProofRecipe) {
  const recipePrimary = await _resolveApiRecipe(proofMeta, type, season, episode);
  if (Array.isArray(recipePrimary) && recipePrimary.length) return recipePrimary;
  if (NIAKVIO_PROVIDER_MODEL.apiRecipe.allowGenericFallback !== true) return [];
}
'''
    new_recipe = '''if (hasProofRecipe) {
  const typedRecipeNeedsTmdb = NIAKVIO_PROVIDER_MODEL.apiRecipe.recipeKind === "typed-resolver-api";
  if (typedRecipeNeedsTmdb && (!proofMeta || !_text(proofMeta.tmdbId))) {
    if (NIAKVIO_PROVIDER_MODEL.apiRecipe.allowGenericFallback !== true) return [];
  } else {
    const recipePrimary = await _resolveApiRecipe(proofMeta, type, season, episode);
    if (Array.isArray(recipePrimary) && recipePrimary.length) return recipePrimary;
    if (NIAKVIO_PROVIDER_MODEL.apiRecipe.allowGenericFallback !== true) return [];
  }
}
'''
    text = once(text, old_recipe, new_recipe, "typed-resolver-empty-tmdb-fail-closed")
    TARGET.write_text(text, encoding="utf-8")
    validate_raw_tmdb(text)
    return True


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    changed = False
    if MARKER not in text:
        text = once(
            text,
            "async function _resolveApiRecipe(meta, mediaType, season, episode) {\n",
            f"/* {MARKER} */\nasync function _resolveApiRecipe(meta, mediaType, season, episode) {{\n",
            "typed-resolver-marker",
        )

        old_gate = '''  const media = _mediaNamespace(mediaType);
  const bases = await _recipeBases(recipe);
  if (!bases.length) return [];
  const values = {'''
        new_gate = '''  const media = _mediaNamespace(mediaType);
  const bases = await _recipeBases(recipe);
  const typedResolverRoute = media === "movie" ? recipe.movieRoute : (recipe.episodeRoute || recipe.movieRoute);
  let typedResolverOrigin = "";
  if (recipe.recipeKind === "typed-resolver-api") {
    try {
      const parsed = new URL(_text(typedResolverRoute));
      if (/^https?:$/i.test(parsed.protocol)) typedResolverOrigin = parsed.origin;
    } catch (_) {}
  }
  if (!bases.length && !typedResolverOrigin) return [];
  const values = {'''
        text = once(text, old_gate, new_gate, "typed-resolver-base-gate")

        text = once(
            text,
            '  if (!recipe.searchRoute) return [];\n',
            '  if (!recipe.searchRoute && !typedResolverOrigin) return [];\n',
            "typed-resolver-search-gate",
        )

        text = once(
            text,
            '  let providerMatch = await findProvider(bases);\n',
            '''  let providerMatch = typedResolverOrigin && !recipe.searchRoute
    ? { id: "", base: typedResolverOrigin }
    : await findProvider(bases);
''',
            "typed-resolver-provider-match",
        )
        TARGET.write_text(text, encoding="utf-8")
        changed = True
    else:
        validate(text)

    changed = _patch_raw_tmdb_route_identity() or changed
    changed = stream_v12.patch() or changed
    # V16 requires the V11 + stream-container state above and is intentionally
    # chained here so targeted/full pipelines cannot drift in execution order.
    changed = authority_v16.patch() or changed
    return changed


def validate_raw_tmdb(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    if value.count(RAW_TMDB_MARKER) != 1:
        raise AssertionError(f"raw TMDB routing marker count={value.count(RAW_TMDB_MARKER)}")
    for needle in (
        'const rawTmdbRouteId = _text(tmdbId).replace(/^tmdb:/i, "").split(":")[0].trim();',
        'if (hasProofRecipe && /^\\d+$/.test(rawTmdbRouteId)) {',
        'tmdbId:rawTmdbRouteId',
        'Object.assign({}, proofMeta, {tmdbId:rawTmdbRouteId})',
        'const typedRecipeNeedsTmdb = NIAKVIO_PROVIDER_MODEL.apiRecipe.recipeKind === "typed-resolver-api";',
        'typedRecipeNeedsTmdb && (!proofMeta || !_text(proofMeta.tmdbId))',
    ):
        if needle not in value:
            raise AssertionError(f"raw TMDB route identity runtime missing: {needle}")


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    if value.count(MARKER) != 1:
        raise AssertionError(f"typed resolver marker count={value.count(MARKER)}")
    for needle in (
        'recipe.recipeKind === "typed-resolver-api"',
        'typedResolverRoute',
        'typedResolverOrigin',
        'if (!bases.length && !typedResolverOrigin) return [];',
        'if (!recipe.searchRoute && !typedResolverOrigin) return [];',
        '? { id: "", base: typedResolverOrigin }',
    ):
        if needle not in value:
            raise AssertionError(f"typed resolver runtime missing: {needle}")
    if 'const bases = await _recipeBases(recipe);\n  if (!bases.length) return [];' in value:
        raise AssertionError("legacy unconditional recipe base gate remains")
    validate_raw_tmdb(value)


def main() -> int:
    changed = patch()
    validate()
    stream_v12.validate()
    authority_v16.validate()
    print(
        f"PROVIDER_BASE_RUNTIME_V11_OK changed={str(changed).lower()} "
        "typed_resolver_api=1 generic_absolute_bypass=0 multi_hop_flattening=0 "
        "stream_containers_v12=1 execution_authority_v16=1 raw_tmdb_route_identity_v19=1 "
        "typed_resolver_empty_tmdb_fail_closed=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
