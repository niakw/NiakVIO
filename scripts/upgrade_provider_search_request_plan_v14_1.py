#!/usr/bin/env python3
"""V14.1: keep search request semantics without promoting transient search hosts.

Two generic corrections:
- only positive source/player resolver hosts may suppress an older runtime domain
  substitution; search/detail success is evidence, not durable host authority;
- HTML catalogue URLs may earn identity score from their anchor label, while all
  existing same-origin/detail eligibility guards remain in force. Explicit movie
  year conflicts remain rejected.

No provider IDs, hostnames, fixtures or provider-specific selectors live here.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECOVERY = ROOT / "scripts" / "recover_provider_routes_from_upstreams.py"
BASE = ROOT / "scripts" / "provider_base_store.py"
RECOVERY_MARKER = "ROUTE_RECOVERY_SEARCH_REQUEST_PLAN_V14_1"
BASE_MARKER = "NIAKVIO_PROVIDER_SEARCH_REQUEST_PLAN_V14_1"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_recovery() -> bool:
    text = RECOVERY.read_text(encoding="utf-8")
    if RECOVERY_MARKER in text:
        validate_recovery(text)
        return False
    if "ROUTE_RECOVERY_SEARCH_REQUEST_PLAN_V14" not in text:
        raise AssertionError("V14.1 requires Search Request Plan V14 first")

    old = '''def _positive_proof_hosts(route_data: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    for row in route_data:
        base = _fresh_positive_origin(row)
        if not base:
            continue
        try:
            host = (urllib.parse.urlsplit(base).hostname or "").casefold()
        except ValueError:
            host = ""
        if host and host not in out:
            out.append(host)
    return out[:24]
'''
    new = '''# ROUTE_RECOVERY_SEARCH_REQUEST_PLAN_V14_1
def _positive_proof_hosts(route_data: list[dict[str, Any]]) -> list[str]:
    """Protect only proof-owned resolver origins from stale domain rewrites.

    Search/detail endpoints can be transient, rate-limited mirrors. Their success
    remains route evidence but cannot revoke an explicit current-domain mapping.
    Source/player origins are terminal resolver authority and may do so.
    """
    out: list[str] = []
    for row in route_data:
        role = str(row.get("role") or "").strip().casefold() if isinstance(row, dict) else ""
        if role not in {"source", "player"}:
            continue
        base = _fresh_positive_origin(row)
        if not base:
            continue
        try:
            host = (urllib.parse.urlsplit(base).hostname or "").casefold()
        except ValueError:
            host = ""
        if host and host not in out:
            out.append(host)
    return out[:24]
'''
    text = once(text, old, new, "resolver-only-proof-authority")
    RECOVERY.write_text(text, encoding="utf-8")
    validate_recovery(text)
    return True


def patch_base() -> bool:
    text = BASE.read_text(encoding="utf-8")
    if BASE_MARKER in text:
        validate_base(text)
        return False
    if "NIAKVIO_PROVIDER_BASE_SEARCH_REQUEST_PLAN_V14" not in text:
        raise AssertionError("V14.1 requires Search Request Plan V14 ProviderBase first")
    if "NIAKVIO_PROVIDER_SOURCE_PLAN_V10" not in text:
        raise AssertionError("V14.1 requires Source Plan V10 first")

    anchor = "function _spv4HtmlDetails(html, base, meta, mediaType, season) {\n"
    helper = r'''/* NIAKVIO_PROVIDER_SEARCH_REQUEST_PLAN_V14_1 */
function _spv14LabelScoreForUrl(html, base, targetUrl, meta, mediaType, season) {
  const target = _text(targetUrl);
  if (!target) return 0;
  const expectedYear = _text(meta && meta.year).slice(0, 4);
  const source = _text(html);
  const pattern = /<a\b([^>]*?)href\s*=\s*["']([^"']+)["']([^>]*)>([\s\S]*?)<\/a>/gi;
  let best = 0;
  let match;
  while ((match = pattern.exec(source))) {
    const candidate = _absolute(match[2], base);
    if (!candidate || candidate !== target) continue;
    const label = _text(match[4])
      .replace(/<[^>]+>/g, " ")
      .replace(/&nbsp;/gi, " ")
      .replace(/&amp;/gi, "&")
      .replace(/\s+/g, " ")
      .trim();
    if (!label) continue;
    let score = _spv4TitleScore(label, meta);
    // A loose token overlap cannot promote a catalogue result by itself.
    if (score < 90) continue;
    const observedYearMatch = label.match(/\b(?:19|20)\d{2}\b/);
    const observedYear = observedYearMatch ? observedYearMatch[0] : "";
    if (mediaType === "movie" && expectedYear && observedYear && observedYear !== expectedYear) continue;
    if (expectedYear && observedYear === expectedYear) score += 40;
    const attrs = _text(match[1]) + " " + _text(match[3]);
    if (/\brel\s*=\s*["'][^"']*\bbookmark\b/i.test(attrs)) score += 24;
    score += _spv10SeasonUrlScore(candidate, mediaType, season);
    best = Math.max(best, score);
  }
  return best;
}
'''
    text = once(text, anchor, helper + anchor, "label-score-helper")

    old_map = '.map(url => ({ url: _substituteDomain(url), score: _spv4UrlScore(url, meta, mediaType, season) }))\n'
    new_map = '''.map(url => ({
url: _substituteDomain(url),
score: Math.max(
_spv4UrlScore(url, meta, mediaType, season),
_spv14LabelScoreForUrl(html, base, url, meta, mediaType, season)
)
}))
'''
    text = once(text, old_map, new_map, "label-aware-html-detail-score")

    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return True


def validate_recovery(text: str | None = None) -> None:
    value = text if text is not None else RECOVERY.read_text(encoding="utf-8")
    for needle in (
        RECOVERY_MARKER,
        'role not in {"source", "player"}',
        "Search/detail endpoints can be transient",
    ):
        if needle not in value:
            raise AssertionError(f"V14.1 recovery missing: {needle}")


def validate_base(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    for needle in (
        BASE_MARKER,
        "function _spv14LabelScoreForUrl",
        "if (score < 90) continue",
        'mediaType === "movie" && expectedYear && observedYear && observedYear !== expectedYear',
        "_spv14LabelScoreForUrl(html, base, url, meta, mediaType, season)",
    ):
        if needle not in value:
            raise AssertionError(f"V14.1 ProviderBase missing: {needle}")


def main() -> int:
    changed = patch_recovery() | patch_base()
    validate_recovery()
    validate_base()
    print(
        f"PROVIDER_SEARCH_REQUEST_PLAN_V14_1_OK changed={str(changed).lower()} "
        "resolver_host_authority_only=1 search_detail_mapping_preserved=1 "
        "label_aware_catalogue_identity=1 movie_year_conflict_rejected=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
