#!/usr/bin/env python3
"""Provider execution authority V16.

Provider-agnostic repair for proof-owned plans that were projected correctly but
executed too late behind broad source-family traversal.

Order after V16:
1. proven API recipe (direct resolver function, not generic getStreams recursion),
2. proven structured Search Request Plan,
3. source-family traversal,
4. legacy/generic fallback already present in ProviderBase.

Explicit player-bearing attributes also receive a reserved crawl pass before
broad HTML URL discovery, preventing UI/navigation links from consuming the
bounded crawler budget first.

No provider ids, hostnames, fixture titles or provider-specific routes live here.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_EXECUTION_AUTHORITY_V16"


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False
    for required in (
        "NIAKVIO_PROVIDER_SOURCE_PLAN_V15",
        "NIAKVIO_PROVIDER_BASE_TYPED_RESOLVER_API_V11",
        "NIAKVIO_PROVIDER_BASE_SEARCH_REQUEST_PLAN_V14",
    ):
        if required not in text:
            raise AssertionError(f"V16 requires {required}")

    # Replace only the V8 proof-recipe wrapper at the start of _spv4GetStreams.
    # Calling _resolveApiRecipe directly prevents generic getStreams from entering
    # unrelated helper/source routes before the proved recipe gets authority.
    pattern = re.compile(
        r'(async function _spv4GetStreams\(tmdbId, mediaType, season, episode\) \{\s*'
        r'const family = _spv4Family\(\);\s*'
        r'const type = _text\(mediaType \|\| "movie"\)\.toLowerCase\(\);\s*)'
        r'/\* NIAKVIO_PROVIDER_BASE_API_RECIPE_FIRST_V8 \*/\s*'
        r'if \(NIAKVIO_PROVIDER_MODEL\.apiRecipe\) \{\s*'
        r'const recipePrimary = await getStreams\(tmdbId, type, season, episode\);\s*'
        r'if \(Array\.isArray\(recipePrimary\) && recipePrimary\.length\) return recipePrimary;\s*'
        r'if \(NIAKVIO_PROVIDER_MODEL\.apiRecipe\.allowGenericFallback !== true\) return \[\];\s*'
        r'\}',
        re.M,
    )
    replacement = r'''\1/* NIAKVIO_PROVIDER_BASE_API_RECIPE_FIRST_V8 */
/* NIAKVIO_PROVIDER_EXECUTION_AUTHORITY_V16 */
const hasProofRecipe = !!NIAKVIO_PROVIDER_MODEL.apiRecipe;
const hasProofSearch = Array.isArray(NIAKVIO_PROVIDER_MODEL.searchRequestPlan) && NIAKVIO_PROVIDER_MODEL.searchRequestPlan.length > 0;
let proofMeta = null;
if (hasProofRecipe || hasProofSearch) proofMeta = await _tmdb(tmdbId, type);
if (hasProofRecipe) {
  const recipePrimary = await _resolveApiRecipe(proofMeta, type, season, episode);
  if (Array.isArray(recipePrimary) && recipePrimary.length) return recipePrimary;
  if (NIAKVIO_PROVIDER_MODEL.apiRecipe.allowGenericFallback !== true) return [];
}
if (hasProofSearch && proofMeta && proofMeta.title) {
  const searchPrimary = await _resolveSearchRequestPlan(proofMeta, type, season, episode);
  if (Array.isArray(searchPrimary) && searchPrimary.length) return searchPrimary;
}'''
    text, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise AssertionError(f"v16-proof-authority: expected one V8 block, got {count}")

    # V15 exposes explicit player attributes, but its broad extraction path may
    # still rank UI/navigation URLs ahead of them. Give explicit player evidence
    # one bounded crawl pass before generic discovery; this does not widen URL
    # eligibility and still requires _crawlDirectMedia to prove terminal media.
    old = '''      const explicitPlayers = _spv15ExplicitPlayerAttrs(html, response.url || detailUrl);
      let urls = _uniq([
        ..._extractUrls(html, response.url || detailUrl),
        ...explicitPlayers
      ]);
'''
    new = '''      const explicitPlayers = _spv15ExplicitPlayerAttrs(html, response.url || detailUrl);
      if (explicitPlayers.length) {
        const explicitCrawled = await _crawlDirectMedia(explicitPlayers, response.url || detailUrl, 3);
        if (explicitCrawled.length) return explicitCrawled.slice(0, 40);
      }
      let urls = _uniq([
        ...explicitPlayers,
        ..._extractUrls(html, response.url || detailUrl)
      ]);
'''
    if text.count(old) != 1:
        raise AssertionError(f"v16-explicit-player-priority: expected one V15 anchor, got {text.count(old)}")
    text = text.replace(old, new, 1)

    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    if value.count(MARKER) != 1:
        raise AssertionError(f"V16 marker count={value.count(MARKER)}")
    required = (
        "const hasProofRecipe = !!NIAKVIO_PROVIDER_MODEL.apiRecipe;",
        "const hasProofSearch = Array.isArray(NIAKVIO_PROVIDER_MODEL.searchRequestPlan)",
        "const recipePrimary = await _resolveApiRecipe(proofMeta, type, season, episode);",
        "const searchPrimary = await _resolveSearchRequestPlan(proofMeta, type, season, episode);",
        "const explicitCrawled = await _crawlDirectMedia(explicitPlayers, response.url || detailUrl, 3);",
        "...explicitPlayers,",
    )
    for needle in required:
        if needle not in value:
            raise AssertionError(f"V16 missing {needle}")
    # The old recursion is forbidden specifically inside the V8/V16 authority
    # prefix because it can invoke helper routes before the proven recipe.
    start = value.index(MARKER)
    end = value.find('if (family === "stremio-json")', start)
    if end < 0:
        raise AssertionError("V16 cannot locate first family traversal")
    prefix = value[start:end]
    if "recipePrimary = await getStreams(" in prefix:
        raise AssertionError("V16 retained recursive generic recipe authority")
    if prefix.index("_resolveApiRecipe") > prefix.index("_resolveSearchRequestPlan"):
        raise AssertionError("V16 recipe must precede SearchRequestPlan")


def main() -> int:
    changed = patch()
    print(
        f"PROVIDER_EXECUTION_AUTHORITY_V16_OK changed={str(changed).lower()} "
        "recipe_first=1 search_plan_second=1 source_family_after=1 explicit_player_reserved_crawl=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
