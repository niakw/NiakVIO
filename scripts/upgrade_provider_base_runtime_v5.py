#!/usr/bin/env python3
'''Upgrade the common ProviderBase reader through cumulative runtime v8 fixes.

The verified v5 upgrader is preserved verbatim in
upgrade_provider_base_runtime_v5_legacy.py. This stable entry point keeps
existing workflows compatible while always applying the current cumulative
reader fixes and shared stream-presentation safety fixes.
'''
from __future__ import annotations

import re

import upgrade_provider_base_runtime_v5_legacy as runtime_v5
import upgrade_provider_base_runtime_v6 as runtime_v6
import upgrade_provider_base_runtime_v7 as runtime_v7
import upgrade_stream_presentation_unknown_quality_v1 as stream_quality_projection


def _once_whitespace_tolerant(text: str, old: str, new: str, label: str) -> str:
    """Match one exact source anchor while ignoring formatting-only whitespace drift."""
    parts = re.split(r'(\s+)', old)
    pattern = ''.join(r'\s+' if part.isspace() else re.escape(part) for part in parts if part)
    matches = list(re.finditer(pattern, text, flags=re.MULTILINE))
    if len(matches) != 1:
        raise AssertionError(f'{label}: expected one whitespace-tolerant anchor, got {len(matches)}')
    match = matches[0]
    return text[:match.start()] + new + text[match.end():]


def _patch_v7_safe_html_text() -> bool:
    """Use the existing deterministic HTML scanner in the DLE title scorer."""
    target = runtime_v7.TARGET
    text = target.read_text(encoding='utf-8')
    unsafe = '_text(match[4]).replace(/<[^>]+>/g, " ")'
    safe = '_htmlVisibleText(match[4])'
    unsafe_count = text.count(unsafe)
    safe_count = text.count(safe)
    if unsafe_count == 0:
        if safe_count != 1:
            raise AssertionError(
                f'v7-safe-html-text: expected one safe scanner when no legacy form remains, got {safe_count}'
            )
        return False
    if unsafe_count != 1:
        raise AssertionError(f'v7-safe-html-text: expected one unsafe anchor, got {unsafe_count}')
    text = text.replace(unsafe, safe, 1)
    target.write_text(text, encoding='utf-8')
    return True


def _patch_v8_api_recipe_precedence() -> bool:
    """An explicit API recipe is executable authority, not a hint after crawling.

    Providers such as Purstream persist a bounded search -> provider id -> typed
    movie/episode recipe. Running the generic sourceRuntimeFamily traversal first
    spends the request budget on the same relative search route expanded against
    site/hub/API origins and can prevent the declared typed route from ever being
    reached. Execute the explicit recipe first; only recipes that explicitly opt
    into generic fallback may continue into source-family discovery.
    """
    target = runtime_v7.TARGET
    text = target.read_text(encoding='utf-8')
    marker = '/* NIAKVIO_PROVIDER_BASE_API_RECIPE_FIRST_V8 */'
    if marker in text:
        if text.count(marker) != 1:
            raise AssertionError(f'v8-api-recipe-first: marker count={text.count(marker)}')
        return False

    old = '''async function _spv4GetStreams(tmdbId, mediaType, season, episode) {
const family = _spv4Family();
const type = _text(mediaType || "movie").toLowerCase();
if (family === "stremio-json") {'''
    new = '''async function _spv4GetStreams(tmdbId, mediaType, season, episode) {
const family = _spv4Family();
const type = _text(mediaType || "movie").toLowerCase();
/* NIAKVIO_PROVIDER_BASE_API_RECIPE_FIRST_V8 */
if (NIAKVIO_PROVIDER_MODEL.apiRecipe) {
const recipePrimary = await getStreams(tmdbId, type, season, episode);
if (Array.isArray(recipePrimary) && recipePrimary.length) return recipePrimary;
if (NIAKVIO_PROVIDER_MODEL.apiRecipe.allowGenericFallback !== true) return [];
}
if (family === "stremio-json") {'''
    text = _once_whitespace_tolerant(text, old, new, 'v8-api-recipe-first')
    target.write_text(text, encoding='utf-8')
    return True


def patch() -> bool:
    changed_v5 = runtime_v5.patch()
    runtime_v5.validate()
    changed_v6 = runtime_v6.patch()
    runtime_v6.validate()
    # Runtime v7 targets the verified v6 JavaScript skeleton. Keep matching
    # fail-closed on tokens/cardinality, but do not bind migrations to indentation.
    runtime_v7.once = _once_whitespace_tolerant
    changed_v7 = runtime_v7.patch()
    changed_safe_html = _patch_v7_safe_html_text()
    changed_recipe_first = _patch_v8_api_recipe_precedence()
    changed_stream_projection = stream_quality_projection.patch()
    return bool(
        changed_v5
        or changed_v6
        or changed_v7
        or changed_safe_html
        or changed_recipe_first
        or changed_stream_projection
    )


def validate() -> None:
    runtime_v5.validate()
    runtime_v6.validate()
    runtime_v7.validate()
    stream_quality_projection.validate()
    text = runtime_v7.TARGET.read_text(encoding='utf-8')
    if '_htmlVisibleText(match[4])' not in text:
        raise AssertionError('runtime v7 DLE parser must use deterministic HTML text scanner')
    if '_text(match[4]).replace(/<[^>]+>/g, " ")' in text:
        raise AssertionError('runtime v7 DLE parser contains forbidden HTML filtering regexp')
    marker = '/* NIAKVIO_PROVIDER_BASE_API_RECIPE_FIRST_V8 */'
    if text.count(marker) != 1:
        raise AssertionError(f'runtime v8 API-recipe precedence marker count={text.count(marker)}')
    recipe_first = text.index(marker)
    family_first = text.index('if (family === "stremio-json")', recipe_first)
    if recipe_first >= family_first:
        raise AssertionError('runtime v8 API recipe must execute before source-family traversal')
    required = (
        'const recipePrimary = await getStreams(tmdbId, type, season, episode);',
        'NIAKVIO_PROVIDER_MODEL.apiRecipe.allowGenericFallback !== true',
    )
    for needle in required:
        if needle not in text[recipe_first:family_first]:
            raise AssertionError(f'runtime v8 API-recipe precedence missing: {needle}')


def main() -> int:
    changed = patch()
    validate()
    print(
        'PROVIDER_BASE_RUNTIME_CURRENT_OK '
        f'changed={str(changed).lower()} v5=1 v6=1 v7=1 v8=1 '
        'external_ids=1 traversal_eligibility=1 nested_priority=1 '
        'source_plan_first=1 api_recipe_first=1 alias_origin=1 dle_runtime=1 safe_html_text=1 '
        'unknown_stream_quality_projection=removed'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
