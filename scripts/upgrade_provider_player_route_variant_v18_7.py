#!/usr/bin/env python3
"""V18.7: prioritize common canonical same-player route representations.

Some file-host players expose an embed/download/e/f/d/file URL that is only a
public landing representation of the actual player page. A common structural
variant uses the same origin and opaque id under /v/. This capability is bounded,
same-origin and data-independent: it contains no provider ids, hosts or fixture
names and never treats the variant itself as playable media.

The canonical /v/<opaque-id> representation is now scheduled before the landing
representation, matching the generic resolver behavior proved by upstream
positive fixtures while preserving the original URL as bounded fallback.

V18.8 is chained here because it operates on the same canonical player response:
a bounded same-origin hidden-form handoff is attempted only after direct and
packed-player extraction miss.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_PLAYER_ROUTE_VARIANT_V18_7"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def _chain_v18_8() -> bool:
    import upgrade_provider_player_form_handoff_v18_8 as v18_8

    changed = v18_8.patch()
    v18_8.validate()
    return changed


def patch() -> bool:
    text = BASE.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return _chain_v18_8()
    if "NIAKVIO_PROVIDER_PACKED_PLAYER_V18_6" not in text:
        raise AssertionError("V18.7 requires V18.6 packed-player decoding")

    anchor = "async function _crawlDirectMedia(seedUrls, referer, maxDepth) {\n"
    helper = r'''/* NIAKVIO_PROVIDER_PLAYER_ROUTE_VARIANT_V18_7 */
function _spv187PlayerRouteVariants(raw) {
  try {
    const parsed = new URL(_text(raw));
    if (!/^https?:$/i.test(parsed.protocol)) return [];
    const original = parsed.toString();
    const nextPath = _text(parsed.pathname).replace(
      /^\/(?:embed|e|f|d|file|download)\/([^/?#]+)\/?$/i,
      "/v/$1"
    );
    if (!nextPath || nextPath === parsed.pathname) return [];
    parsed.pathname = nextPath;
    parsed.hash = "";
    const next = _crawlCanonical(parsed.toString());
    return next && next !== _crawlCanonical(original) ? [next] : [];
  } catch (_) {
    return [];
  }
}
function _spv187PrioritizedPlayerRoutes(values) {
  const out = [];
  for (const raw of values || []) {
    const canonical = _crawlCanonical(raw);
    if (!canonical) continue;
    for (const variant of _spv187PlayerRouteVariants(canonical)) out.push(variant);
    out.push(canonical);
  }
  return _uniq(out);
}
function _spv187QueueScore(url) {
  let bonus = 0;
  try {
    const path = _text(new URL(url).pathname);
    if (/^\/v\/[A-Za-z0-9_-]{3,160}\/?$/i.test(path)) bonus = 1000;
  } catch (_) {}
  return _crawlUrlScore(url) + bonus;
}
'''
    text = once(text, anchor, helper + anchor, "v18.7-player-route-helper")

    text = once(
        text,
        "  const queue = _uniq(seedUrls.map(_crawlCanonical)).filter(Boolean).filter(_crawlEligible).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a)).slice(0, 8).map(url => ({ url, depth: 0, referer }));\n",
        "  const queue = _spv187PrioritizedPlayerRoutes(seedUrls).filter(_crawlEligible).sort((a,b)=>_spv187QueueScore(b)-_spv187QueueScore(a)).slice(0, 8).map(url => ({ url, depth: 0, referer }));\n",
        "v18.7-prioritize-initial-player-route",
    )
    text = once(
        text,
        "    queue.sort((a,b)=>_crawlUrlScore(b.url)-_crawlUrlScore(a.url));\n",
        "    queue.sort((a,b)=>_spv187QueueScore(b.url)-_spv187QueueScore(a.url));\n",
        "v18.7-prioritize-canonical-queue",
    )

    old = '''      const direct = urls.filter(_directMedia);
      if (direct.length) {
        streams.push(..._streams(direct, responseUrl));
        continue;
      }
      if (row.depth < Math.max(0, Number(maxDepth) || 0)) {
'''
    new = '''      const direct = urls.filter(_directMedia);
      if (direct.length) {
        streams.push(..._streams(direct, responseUrl));
        continue;
      }
      // Preserve the landing URL as fallback, but always prioritize the same
      // opaque id under the canonical /v/ representation when structurally safe.
      for (const variant of _spv187PlayerRouteVariants(responseUrl)) {
        if (!seen.has(variant)) queue.push({ url: variant, depth: row.depth, referer: responseUrl });
      }
      if (row.depth < Math.max(0, Number(maxDepth) || 0)) {
'''
    text = once(text, old, new, "v18.7-enqueue-player-route-variant")
    BASE.write_text(text, encoding="utf-8")
    validate(text)
    _chain_v18_8()
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    if value.count(MARKER) != 1:
        raise AssertionError(f"V18.7 marker count={value.count(MARKER)}")
    for needle in (
        "function _spv187PlayerRouteVariants(raw)",
        "function _spv187PrioritizedPlayerRoutes(values)",
        "function _spv187QueueScore(url)",
        '^\\/(?:embed|e|f|d|file|download)\\/([^/?#]+)\\/?$',
        '"/v/$1"',
        "_spv187PrioritizedPlayerRoutes(seedUrls)",
        "_spv187QueueScore(b.url)-_spv187QueueScore(a.url)",
        "for (const variant of _spv187PlayerRouteVariants(responseUrl))",
        "depth: row.depth, referer: responseUrl",
    ):
        if needle not in value:
            raise AssertionError(f"V18.7 missing {needle}")
    section = value.split("/* NIAKVIO_PROVIDER_PLAYER_ROUTE_VARIANT_V18_7 */", 1)[1].split(
        "async function _crawlDirectMedia", 1
    )[0].casefold()
    for forbidden in (
        "mugiwara",
        "smoothpre",
        "ansembed",
        "jujutsu",
        "vidhide",
    ):
        if forbidden in section:
            raise AssertionError(f"V18.7 provider-specific token leaked: {forbidden}")


def main() -> int:
    changed = patch()
    print(
        f"PROVIDER_PLAYER_ROUTE_VARIANT_V18_7_OK changed={str(changed).lower()} "
        "same_origin=1 opaque_id_preserved=1 canonical_first=1 landing_fallback=1 "
        "crawl_depth_cost=0 form_handoff_v18_8=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
