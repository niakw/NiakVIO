#!/usr/bin/env python3
"""Source Plan V15: bounded player attributes and catalogue-card identity.

Provider-agnostic runtime improvements derived from positive multi-hop proofs:
- only explicit URL-bearing attributes are treated as URLs; arbitrary data-* UI
  values must never consume the bounded crawl budget;
- explicit player-bearing data-* attributes are eligible crawl seeds;
- the current proven search response origin is a valid catalogue origin for the
  result page being parsed, without promoting it to durable global authority;
- short third-party /e/<id> resolver URLs can be crawled after provider identity
  has already been established on the detail page;
- catalogue <article> cards may contribute title/year identity to a same-origin
  detail URL, without allowing a loose URL/token match or a conflicting movie year.

No provider IDs, hostnames or fixture titles are encoded here.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_SOURCE_PLAN_V15"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_base() -> bool:
    text = BASE.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False
    if "NIAKVIO_PROVIDER_SEARCH_REQUEST_PLAN_V14_1" not in text:
        raise AssertionError("Source Plan V15 requires V14.1 first")

    # A current search response is already proof that its own origin is valid for
    # links found in that response. Accept that local origin without teaching it
    # as a durable provider base or weakening the normal runtime-base check.
    text = once(
        text,
        '''function _spv4SameProviderOrigin(url) {\nconst candidate = _origin(_substituteDomain(url));\nreturn !!candidate && _runtimeBases().some(base => _origin(_substituteDomain(base)) === candidate);\n}\n''',
        '''function _spv4SameProviderOrigin(url, currentBase) {\nconst candidate = _origin(_substituteDomain(url));\nconst current = _origin(_substituteDomain(currentBase));\nif (candidate && current && candidate === current) return true;\nreturn !!candidate && _runtimeBases().some(base => _origin(_substituteDomain(base)) === candidate);\n}\n''',
        "v15-current-response-origin",
    )

    # Earlier Source Plan versions accepted every data-* attribute. Values such as
    # language codes, tooltip directions and booleans then became fake relative
    # URLs. Keep only fields whose semantics explicitly carry a URL/player.
    text = once(
        text,
        '''  const re = /(?:src|href|file|url|data-[a-z0-9_:-]+)\\s*=\\s*["']([^"']+)["']/gi;\n''',
        '''  const re = /(?:src|href|file|url|data-(?:src|url|video|embed|player|file|stream|link|href))\\s*=\\s*["']([^"']+)["']/gi;\n''',
        "v15-narrow-attribute-urls",
    )

    # The generic HTML/JS extractor must see the same explicit player attributes;
    # this is used after identity is established and before the bounded crawler.
    text = once(
        text,
        '''    /(?:src|href|file|url|pathname|permalink|embedUrl|embed_url|contentUrl)\\s*["']?\\s*[:=]\\s*["']([^"'<>\\s]+)["']/gi,\n''',
        '''    /(?:src|href|file|url|pathname|permalink|embedUrl|embed_url|contentUrl|data-(?:src|url|video|embed|player|file|stream|link|href))\\s*["']?\\s*[:=]\\s*["']([^"'<>\\s]+)["']/gi,\n''',
        "v15-generic-explicit-player-attrs",
    )

    helper_anchor = "function _spv4HtmlDetails(html, base, meta, mediaType, season) {\n"
    helpers = r'''/* NIAKVIO_PROVIDER_SOURCE_PLAN_V15 */
function _spv15ExplicitPlayerAttrs(html, base) {
  const out = [];
  const source = _embeddedText(html);
  const re = /\bdata-(?:video|embed|player|src|url|file|stream|link|href)\s*=\s*["']([^"']+)["']/gi;
  let match;
  while ((match = re.exec(source)) !== null) {
    const absolute = _absolute(match[1], base);
    if (absolute && /^https?:/i.test(absolute)) out.push(absolute);
    if (out.length >= 32) break;
  }
  return _uniq(out);
}
function _spv15ArticleDetails(html, base, meta, mediaType, season) {
  const out = [];
  const source = _text(html);
  const expectedYear = _text(meta && meta.year).slice(0, 4);
  const articleRe = /<article\b[^>]*>[\s\S]{0,12000}?<\/article>/gi;
  let article;
  while ((article = articleRe.exec(source)) !== null) {
    const block = article[0];
    const visible = _htmlVisibleText(block).replace(/\s+/g, " ").trim();
    let identityScore = _spv4TitleScore(visible, meta);
    if (identityScore < 90) continue;
    const years = [];
    const yearRe = /\b(?:19|20)\d{2}\b/g;
    let yearMatch;
    while ((yearMatch = yearRe.exec(visible)) !== null) {
      if (!years.includes(yearMatch[0])) years.push(yearMatch[0]);
      if (years.length >= 6) break;
    }
    if (mediaType === "movie" && expectedYear && years.length && !years.includes(expectedYear)) continue;
    if (expectedYear && years.includes(expectedYear)) identityScore += 40;
    const hrefRe = /<a\b([^>]*?)href\s*=\s*["']([^"']+)["']([^>]*)>/gi;
    let link;
    while ((link = hrefRe.exec(block)) !== null) {
      const url = _absolute(link[2], base);
      if (!url || !_spv4SameProviderOrigin(url, base) || !_spv7DetailUrlEligible(url)) continue;
      const attrs = _text(link[1]) + " " + _text(link[3]);
      const bookmark = /\brel\s*=\s*["'][^"']*\bbookmark\b/i.test(attrs);
      const urlScore = _spv4UrlScore(url, meta, mediaType, season);
      if (!bookmark && urlScore < 36) continue;
      out.push({
        url: _substituteDomain(url),
        score: Math.max(identityScore, urlScore) + (bookmark ? 24 : 0) + _spv10SeasonUrlScore(url, mediaType, season)
      });
      if (out.length >= 24) break;
    }
    if (out.length >= 24) break;
  }
  return out;
}
'''
    text = once(text, helper_anchor, helpers + helper_anchor, "v15-runtime-helpers")

    # V14.1 has already made the base catalogue matcher label-aware. Merge
    # article-card evidence while preserving URL eligibility and identity gates.
    pattern = re.compile(
        r"function _spv4HtmlDetails\(html, base, meta, mediaType, season\) \{\n"
        r"[\s\S]*?\n\}\nfunction _spv4JsonRows\(value, out\) \{",
        re.M,
    )
    replacement = r'''function _spv4HtmlDetails(html, base, meta, mediaType, season) {
  const rows = _spv4AttrUrls(html, base)
    .filter(url => _spv4SameProviderOrigin(url, base))
    .filter(_spv7DetailUrlEligible)
    .map(url => ({
      url: _substituteDomain(url),
      score: Math.max(
        _spv4UrlScore(url, meta, mediaType, season),
        _spv14LabelScoreForUrl(html, base, url, meta, mediaType, season)
      )
    }))
    .filter(row => row.score >= 36);
  rows.push(..._spv15ArticleDetails(html, base, meta, mediaType, season));
  const best = new Map();
  for (const row of rows) {
    if (!row || !row.url) continue;
    const previous = best.get(row.url);
    if (!previous || Number(row.score || 0) > Number(previous.score || 0)) best.set(row.url, row);
  }
  return [...best.values()]
    .sort((a, b) => b.score - a.score)
    .map(row => row.url)
    .slice(0, 8);
}
function _spv4JsonRows(value, out) {'''
    text, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise AssertionError(f"v15-html-details: expected one function, got {count}")

    # V12 already owns the /file resolver extension. Preserve it while adding
    # only the common short third-party /e/<id> resolver form.
    old_player = '''    return /\\/(?:watch|embed|player|play|video|videos|stream|streams|source|sources|server|servers|resolve|proxy|drive|download|file|files)(?:[/?#.-]|$)/i.test(parsed.pathname + parsed.search);\n'''
    new_player = '''    const providerOrigin = _runtimeBases().some(base => _origin(base) === parsed.origin);\n    if (!providerOrigin && /^\\/e\\/[^/?#]+(?:[/?#]|$)/i.test(parsed.pathname + parsed.search)) return true;\n    return /\\/(?:watch|embed|player|play|video|videos|stream|streams|source|sources|server|servers|resolve|proxy|drive|download|file|files)(?:[/?#.-]|$)/i.test(parsed.pathname + parsed.search);\n'''
    text = once(text, old_player, new_player, "v15-third-party-short-embed")

    old_urls = '''      let urls = _extractUrls(html, response.url || detailUrl);\n'''
    new_urls = '''      const explicitPlayers = _spv15ExplicitPlayerAttrs(html, response.url || detailUrl);\n      let urls = _uniq([\n        ..._extractUrls(html, response.url || detailUrl),\n        ...explicitPlayers\n      ]);\n'''
    text = once(text, old_urls, new_urls, "v15-detail-player-attrs")

    BASE.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    for needle in (
        MARKER,
        "function _spv15ExplicitPlayerAttrs",
        "function _spv15ArticleDetails",
        "function _spv4SameProviderOrigin(url, currentBase)",
        "candidate === current",
        "data-(?:src|url|video|embed|player|file|stream|link|href)",
        "_spv4SameProviderOrigin(url, base)",
        "rows.push(..._spv15ArticleDetails",
        "...explicitPlayers",
        "providerOrigin",
    ):
        if needle not in value:
            raise AssertionError(f"V15 ProviderBase missing: {needle}")
    if "data-[a-z0-9_:-]+" in value:
        raise AssertionError("V15 ProviderBase still contains generic data-* URL extraction")


def main() -> int:
    changed = patch_base()
    validate()
    print(
        f"PROVIDER_SOURCE_PLAN_V15_OK changed={str(changed).lower()} "
        "explicit_player_attrs=1 current_search_origin=1 noisy_data_attrs_rejected=1 "
        "third_party_short_embed=1 catalogue_article_identity=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
