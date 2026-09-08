#!/usr/bin/env python3
"""Search Plan V17: bridge proven catalogue search into the canonical detail resolver.

V14 made structured search requests executable, but its result path sent proven
catalogue detail URLs directly to the bounded player crawler. That skipped the
canonical detail resolver (episode selection, DLE film API, explicit data-video,
nested players) and also allowed a freshly observed same-origin detail URL to be
rewritten immediately by historical domain substitutions.

V17 keeps the fresh response origin only for same-origin catalogue links and,
after positive catalogue identity, resolves each detail through
_spv4ResolveDetail before falling back to the player crawler.

V18/V18.1/V18.2/V18.4 are chained from this canonical owner so every V17 consumer
also receives the proof-correlated provider-value DATA plan, provider-native JSON
identity scoring, V16 proof authority, and JSON-text identity decoding.
No provider ids, hosts, fixture titles or provider-specific routes are encoded.
"""
from __future__ import annotations

from pathlib import Path

import upgrade_provider_correlated_value_plan_v18 as v18
import upgrade_provider_correlated_value_plan_v18_1 as v18_1
import upgrade_provider_correlated_value_authority_v18_2 as v18_2
import upgrade_provider_correlated_value_json_text_v18_4 as v18_4

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_SEARCH_DETAIL_BRIDGE_V17"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch() -> bool:
    text = BASE.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False
    for required in (
        "NIAKVIO_PROVIDER_SOURCE_PLAN_V15",
        "NIAKVIO_PROVIDER_EXECUTION_AUTHORITY_V16",
        "NIAKVIO_PROVIDER_BASE_SEARCH_REQUEST_PLAN_V14",
    ):
        if required not in text:
            raise AssertionError(f"V17 requires {required}")

    helper_anchor = "function _spv15ArticleDetails(html, base, meta, mediaType, season) {\n"
    helper = r'''/* NIAKVIO_PROVIDER_SEARCH_DETAIL_BRIDGE_V17 */
function _spv17CurrentResponseUrl(value, base) {
  try {
    const raw = new URL(value, base).toString();
    const current = new URL(base).origin;
    if (new URL(raw).origin === current) return raw;
  } catch (_) {}
  return _absolute(value, base);
}
'''
    text = once(text, helper_anchor, helper + helper_anchor, "v17-current-response-helper")

    old_article = '''      const url = _absolute(link[2], base);
      if (!url || !_spv4SameProviderOrigin(url, base) || !_spv7DetailUrlEligible(url)) continue;
'''
    new_article = '''      const url = _spv17CurrentResponseUrl(link[2], base);
      if (!url || !_spv4SameProviderOrigin(url, base) || !_spv7DetailUrlEligible(url)) continue;
'''
    text = once(text, old_article, new_article, "v17-preserve-current-article-origin")

    old_push = '''      out.push({
        url: _substituteDomain(url),
        score: Math.max(identityScore, urlScore) + (bookmark ? 24 : 0) + _spv10SeasonUrlScore(url, mediaType, season)
      });
'''
    new_push = '''      out.push({
        url,
        score: Math.max(identityScore, urlScore) + (bookmark ? 24 : 0) + _spv10SeasonUrlScore(url, mediaType, season)
      });
'''
    text = once(text, old_push, new_push, "v17-article-return-live-origin")

    old_bridge = '''      if (details.length) {
        const crawled = await _crawlDirectMedia(_uniq(details).slice(0, 8), payload.base || url, 3);
        if (crawled.length) return crawled.slice(0, 40);
      }
'''
    new_bridge = '''      if (details.length) {
        const family = _spv4Family();
        for (const detailUrl of _uniq(details).slice(0, 8)) {
          const detailStreams = await _spv4ResolveDetail(
            detailUrl,
            meta,
            mediaType,
            season,
            episode,
            family
          );
          if (Array.isArray(detailStreams) && detailStreams.length) return detailStreams.slice(0, 40);
        }
        const crawled = await _crawlDirectMedia(_uniq(details).slice(0, 8), payload.base || url, 3);
        if (crawled.length) return crawled.slice(0, 40);
      }
'''
    text = once(text, old_bridge, new_bridge, "v17-search-to-detail-resolver")

    BASE.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    if value.count(MARKER) != 1:
        raise AssertionError(f"V17 marker count={value.count(MARKER)}")
    for needle in (
        "function _spv17CurrentResponseUrl",
        "if (new URL(raw).origin === current) return raw;",
        "const url = _spv17CurrentResponseUrl(link[2], base);",
        "const family = _spv4Family();",
        "const detailStreams = await _spv4ResolveDetail(",
        "const crawled = await _crawlDirectMedia(_uniq(details).slice(0, 8)",
    ):
        if needle not in value:
            raise AssertionError(f"V17 missing {needle}")
    if 'url: _substituteDomain(url),\n        score: Math.max(identityScore' in value:
        raise AssertionError("V17 article detail still rewrites the current live origin")


def main() -> int:
    changed = patch()
    v18_changed = v18.patch_recovery() | v18.patch_materializer() | v18.patch_base()
    v18.validate_recovery()
    v18.validate_materializer()
    v18.validate_base()
    v18_1_changed = v18_1.patch()
    v18_1.validate()
    v18_2_changed = v18_2.patch()
    v18_2.validate()
    v18_4_changed = v18_4.patch()
    v18_4.validate()
    print(
        f"PROVIDER_SEARCH_DETAIL_BRIDGE_V17_OK changed={str(changed).lower()} "
        "current_origin_preserved=1 canonical_detail_resolver=1 player_crawl_fallback=1 provider_specific_rules=0"
    )
    print(
        f"PROVIDER_CORRELATED_VALUE_PLAN_V18_OK changed={str(v18_changed).lower()} "
        "provider_value_dataflow=1 semantic_positive_only=1 exact_proof_base=1 "
        "all_html_current_origin=1 provider_specific_rules=0"
    )
    print(
        f"PROVIDER_CORRELATED_VALUE_PLAN_V18_1_OK changed={str(v18_1_changed).lower()} "
        "scored_json_slug_identity=1 all_identity_labels_scored=1 bounded_charset=1 "
        "html_slug_inference=0 provider_specific_rules=0"
    )
    print(
        f"PROVIDER_CORRELATED_VALUE_AUTHORITY_V18_2_OK changed={str(v18_2_changed).lower()} "
        "provider_value_first=1 recipe_second=1 search_third=1 family_after=1 "
        "provider_specific_rules=0"
    )
    print(
        f"PROVIDER_CORRELATED_VALUE_JSON_TEXT_V18_4_OK changed={str(v18_4_changed).lower()} "
        "json_text_first=1 strict_v18_identity_reused=1 html_fallback=1 bounded_payload=1 "
        "provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
