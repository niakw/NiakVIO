#!/usr/bin/env python3
'''Upgrade the common ProviderBase reader through cumulative runtime v9 fixes.

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


def _patch_v9_no_episodic_year_identity() -> bool:
    """Keep release-year identity strictly movie-only.

    TV/series/anime identity is title/type plus season+episode. Series origin
    year and season/episode year are intentionally ignored by ProviderBase
    acceptance logic because provider catalogues may expose either one.
    """
    target = runtime_v7.TARGET
    text = target.read_text(encoding='utf-8')
    marker = '/* NIAKVIO_PROVIDER_BASE_NO_EPISODIC_YEAR_V9 */'
    if marker in text:
        if text.count(marker) != 1:
            raise AssertionError(f'v9-no-episodic-year: marker count={text.count(marker)}')
        return False

    old_score = '''function _recipeScore(row, meta, recipe, expectedMedia) {
  const title = _slug(_recipeValue(row, recipe.titleFields || ["title","name","post_title","original_title"]));
  const expectedTitles = _uniq([meta && meta.title, ...((meta && Array.isArray(meta.aliases)) ? meta.aliases : [])])
    .map(_slug).filter(Boolean);
  const expected = expectedTitles[0] || "";
  const actualMedia = _recipeMediaType(row, recipe);
  const year = _recipeValue(row, recipe.yearFields || ["year","release_date","first_air_date"]).slice(0, 4);
  const expectedYear = _text(meta && meta.year).slice(0, 4);
  const providerId = _recipeValue(row, recipe.idFields || ["id","_id","media_id","post_id"]);

  if (recipe.strictIdentity) {
    if (!providerId || !title || !expectedTitles.length || !expectedTitles.includes(title)) return -1;
    if (actualMedia && expectedMedia && actualMedia !== expectedMedia) return -1;
    if (recipe.requireProviderTypeEvidence === true && (!actualMedia || !expectedMedia)) return -1;
    if (expectedYear) {
      if (!year || !/^\\d{4}$/.test(year)) return -1;
      if (Math.abs(Number(year) - Number(expectedYear)) > 1) return -1;
    }
    return 100 + (year === expectedYear ? 20 : 10) + 20;
  }

  if (actualMedia && expectedMedia && actualMedia !== expectedMedia) return -1;
  if (year && expectedYear && year !== expectedYear) return -1;
  let score = 0;
  if (title && expected && title === expected) score += 200;
  else if (title && expected && (title.includes(expected) || expected.includes(title))) score += 90;
  if (title && expected) {
    for (const token of expected.split("-").filter(value => value.length >= 3)) {
      if (title.includes(token)) score += 10;
    }
  }
  if (year && expectedYear && year === expectedYear) score += 40;
  if (actualMedia && expectedMedia && actualMedia === expectedMedia) score += 60;
  if (providerId) score += 15;
  return score;
}'''
    new_score = '''/* NIAKVIO_PROVIDER_BASE_NO_EPISODIC_YEAR_V9 */
function _recipeScore(row, meta, recipe, expectedMedia) {
  const title = _slug(_recipeValue(row, recipe.titleFields || ["title","name","post_title","original_title"]));
  const expectedTitles = _uniq([meta && meta.title, ...((meta && Array.isArray(meta.aliases)) ? meta.aliases : [])])
    .map(_slug).filter(Boolean);
  const expected = expectedTitles[0] || "";
  const actualMedia = _recipeMediaType(row, recipe);
  const year = _recipeValue(row, recipe.yearFields || ["year","release_date","first_air_date"]).slice(0, 4);
  const expectedYear = _text(meta && meta.year).slice(0, 4);
  const providerId = _recipeValue(row, recipe.idFields || ["id","_id","media_id","post_id"]);
  const movieIdentity = expectedMedia === "movie";

  if (recipe.strictIdentity) {
    if (!providerId || !title || !expectedTitles.length || !expectedTitles.includes(title)) return -1;
    if (actualMedia && expectedMedia && actualMedia !== expectedMedia) return -1;
    if (recipe.requireProviderTypeEvidence === true && (!actualMedia || !expectedMedia)) return -1;
    if (movieIdentity && expectedYear) {
      if (!year || !/^\\d{4}$/.test(year)) return -1;
      if (Math.abs(Number(year) - Number(expectedYear)) > 1) return -1;
    }
    return 120 + (movieIdentity && year === expectedYear ? 20 : 0);
  }

  if (actualMedia && expectedMedia && actualMedia !== expectedMedia) return -1;
  if (movieIdentity && year && expectedYear && year !== expectedYear) return -1;
  let score = 0;
  if (title && expected && title === expected) score += 200;
  else if (title && expected && (title.includes(expected) || expected.includes(title))) score += 90;
  if (title && expected) {
    for (const token of expected.split("-").filter(value => value.length >= 3)) {
      if (title.includes(token)) score += 10;
    }
  }
  if (movieIdentity && year && expectedYear && year === expectedYear) score += 40;
  if (actualMedia && expectedMedia && actualMedia === expectedMedia) score += 60;
  if (providerId) score += 15;
  return score;
}'''
    text = _once_whitespace_tolerant(text, old_score, new_score, 'v9-recipe-year-movie-only')

    old_html = '''function _strictHtmlIdentityOk(html, meta) {
  if (!NIAKVIO_PROVIDER_MODEL.strictHtmlIdentity) return true;
  if (!meta || !meta.title) return false;
  const visible = _htmlVisibleText(html);
  const normalized = _slug(visible);
  const titles = _uniq([meta.title, ...((Array.isArray(meta.aliases) ? meta.aliases : []))])
    .map(_slug)
    .filter(Boolean);
  if (!titles.length || !titles.some(title => normalized.includes(title))) return false;
  const year = _text(meta.year).slice(0, 4);
  if (year && /^\\d{4}$/.test(year)) {
    const years = _text(html).match(/\\b(?:19|20)\\d{2}\\b/g) || [];
    if (years.length && !years.includes(year)) return false;
  }
  return true;
}'''
    new_html = '''function _strictHtmlIdentityOk(html, meta, mediaType) {
  if (!NIAKVIO_PROVIDER_MODEL.strictHtmlIdentity) return true;
  if (!meta || !meta.title) return false;
  const visible = _htmlVisibleText(html);
  const normalized = _slug(visible);
  const titles = _uniq([meta.title, ...((Array.isArray(meta.aliases) ? meta.aliases : []))])
    .map(_slug)
    .filter(Boolean);
  if (!titles.length || !titles.some(title => normalized.includes(title))) return false;
  if (_mediaNamespace(mediaType) === "movie") {
    const year = _text(meta.year).slice(0, 4);
    if (year && /^\\d{4}$/.test(year)) {
      const years = _text(html).match(/\\b(?:19|20)\\d{2}\\b/g) || [];
      if (years.length && !years.includes(year)) return false;
    }
  }
  return true;
}'''
    text = _once_whitespace_tolerant(text, old_html, new_html, 'v9-html-year-movie-only')
    text = _once_whitespace_tolerant(
        text,
        'if (!_strictHtmlIdentityOk(html, meta)) continue;',
        'if (!_strictHtmlIdentityOk(html, meta, mediaType)) continue;',
        'v9-html-year-call-media-type',
    )
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
    changed_no_episodic_year = _patch_v9_no_episodic_year_identity()
    changed_stream_projection = stream_quality_projection.patch()
    return bool(
        changed_v5
        or changed_v6
        or changed_v7
        or changed_safe_html
        or changed_recipe_first
        or changed_no_episodic_year
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

    v9 = '/* NIAKVIO_PROVIDER_BASE_NO_EPISODIC_YEAR_V9 */'
    if text.count(v9) != 1:
        raise AssertionError(f'runtime v9 no-episodic-year marker count={text.count(v9)}')
    required_v9 = (
        'const movieIdentity = expectedMedia === "movie";',
        'if (movieIdentity && expectedYear)',
        'if (movieIdentity && year && expectedYear && year !== expectedYear) return -1;',
        'if (_mediaNamespace(mediaType) === "movie")',
        'if (!_strictHtmlIdentityOk(html, meta, mediaType)) continue;',
    )
    for needle in required_v9:
        if needle not in text:
            raise AssertionError(f'runtime v9 no-episodic-year missing: {needle}')
    forbidden_v9 = (
        'if (year && expectedYear && year !== expectedYear) return -1;',
        'if (!_strictHtmlIdentityOk(html, meta)) continue;',
    )
    for needle in forbidden_v9:
        if needle in text:
            raise AssertionError(f'runtime v9 retained episodic year-sensitive legacy path: {needle}')


def main() -> int:
    changed = patch()
    validate()
    print(
        'PROVIDER_BASE_RUNTIME_CURRENT_OK '
        f'changed={str(changed).lower()} v5=1 v6=1 v7=1 v8=1 v9=1 '
        'external_ids=1 traversal_eligibility=1 nested_priority=1 '
        'source_plan_first=1 api_recipe_first=1 alias_origin=1 dle_runtime=1 safe_html_text=1 '
        'episodic_year_checks=0 movie_year_identity=1 unknown_stream_quality_projection=removed'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
