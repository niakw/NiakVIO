#!/usr/bin/env python3
"""Allow proof-v5 absolute API recipes to execute without a separate base/search route.

A provider may expose fully-qualified movie/episode/direct routes. Those routes are
already executable authority and must not be rejected merely because the recipe has
no separate `base` or `searchRoute`. Provider-id-dependent routes still require a
search/provider-id step; this migration does not guess provider ids.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_BASE_ABSOLUTE_RECIPE_V11"


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
        "absolute-recipe-marker",
    )

    old_gate = '''const media = _mediaNamespace(mediaType);
const bases = await _recipeBases(recipe);
if (!bases.length) return [];
const values = {'''
    new_gate = '''const media = _mediaNamespace(mediaType);
const bases = await _recipeBases(recipe);
function _recipeBasesFor(pattern) {
  if (bases.length) return bases;
  try {
    const route = _text(pattern);
    if (/^https?:\\/\\//i.test(route)) return [new URL(route).origin];
  } catch (_) {}
  return [];
}
const hasExecutableRecipeOrigin = [
  recipe.directRoute, recipe.searchRoute, recipe.movieRoute, recipe.episodeRoute
].some(pattern => _recipeBasesFor(pattern).length > 0);
if (!bases.length && !hasExecutableRecipeOrigin) return [];
const values = {'''
    text = once(text, old_gate, new_gate, "absolute-recipe-base-gate")

    text = once(
        text,
        "for (const base of bases.slice(0, 2)) {",
        "for (const base of _recipeBasesFor(recipe.directRoute).slice(0, 2)) {",
        "absolute-direct-route-bases",
    )

    old_search_guard = 'if (!recipe.searchRoute) return [];\n'
    new_search_guard = '''const typedRouteWithoutSearch = media === "movie"
  ? recipe.movieRoute
  : (recipe.episodeRoute || recipe.movieRoute);
const typedRouteNeedsProviderId = /\\{(?:id|providerId)\\}/i.test(_text(typedRouteWithoutSearch));
if (!recipe.searchRoute && (!typedRouteWithoutSearch || typedRouteNeedsProviderId)) return [];
'''
    text = once(text, old_search_guard, new_search_guard, "absolute-typed-route-search-guard")

    text = once(
        text,
        "let providerMatch = await findProvider(bases);",
        '''let providerMatch = recipe.searchRoute
  ? await findProvider(_recipeBasesFor(recipe.searchRoute))
  : { id: values.providerId, base: _recipeBasesFor(typedRouteWithoutSearch)[0] || "" };''',
        "absolute-typed-route-provider-match",
    )

    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    if value.count(MARKER) != 1:
        raise AssertionError(f"absolute recipe marker count={value.count(MARKER)}")
    for needle in (
        "function _recipeBasesFor(pattern)",
        "hasExecutableRecipeOrigin",
        "_recipeBasesFor(recipe.directRoute).slice(0, 2)",
        "typedRouteWithoutSearch",
        "typedRouteNeedsProviderId",
        "await findProvider(_recipeBasesFor(recipe.searchRoute))",
        '_recipeBasesFor(typedRouteWithoutSearch)[0] || ""',
    ):
        if needle not in value:
            raise AssertionError(f"absolute recipe runtime missing: {needle}")
    old = "const bases = await _recipeBases(recipe);\nif (!bases.length) return [];"
    if old in value:
        raise AssertionError("legacy unconditional recipe base gate remains")


def main() -> int:
    changed = patch()
    print(
        f"PROVIDER_BASE_RUNTIME_V11_OK changed={str(changed).lower()} "
        "absolute_direct=1 absolute_typed=1 provider_id_guessing=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
