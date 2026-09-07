#!/usr/bin/env python3
"""Execute explicitly classified typed resolver APIs without a search/base phase.

This is intentionally narrower than "absolute URL means executable". Recognition
must first classify a recipe as `typed-resolver-api`: a TMDB-addressable movie/TV
resolver whose selected provider request is terminal and already produced streams.
Multi-hop/player/search providers (VidSrc-like families included) keep their own
source plan and are never flattened by this migration.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_BASE_TYPED_RESOLVER_API_V11"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False

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
    validate(text)
    return True


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


def main() -> int:
    changed = patch()
    print(
        f"PROVIDER_BASE_RUNTIME_V11_OK changed={str(changed).lower()} "
        "typed_resolver_api=1 generic_absolute_bypass=0 multi_hop_flattening=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
