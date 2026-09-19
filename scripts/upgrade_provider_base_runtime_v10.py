#!/usr/bin/env python3
"""ProviderBase runtime v10: reject unrelated bare external crawl roots.

A bare external origin is normally a landing/decorative link, not a resolver.
Following it can consume the entire provider deadline and discard already found
results. Direct media and meaningful resolver/player paths remain eligible.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_BASE_BOUNDED_EXTERNAL_ROOT_V10"


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
    crawl_anchor = "async function _crawlDirectMedia(seedUrls, referer, maxDepth) {"
    helper = r'''/* NIAKVIO_PROVIDER_BASE_BOUNDED_EXTERNAL_ROOT_V10 */
function _crawlFollowable(url, fromUrl) {
  if (!_crawlEligible(url)) return false;
  if (_directMedia(url)) return true;
  try {
    const next = new URL(url);
    const from = new URL(fromUrl);
    const rootOnly = (next.pathname === "/" || next.pathname === "") && !next.search && !next.hash;
    if (rootOnly && next.origin !== from.origin) return false;
    return true;
  } catch (_) { return false; }
}
'''
    text = once(text, crawl_anchor, helper + crawl_anchor, "bounded-root-helper-boundary")
    old = '_uniq(urls.map(_crawlCanonical)).filter(Boolean).filter(_crawlEligible).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a))'
    new = '_uniq(urls.map(_crawlCanonical)).filter(Boolean).filter(next=>_crawlFollowable(next,responseUrl)).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a))'
    text = once(text, old, new, "bounded-external-root-crawl")
    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    if value.count(MARKER) != 1:
        raise AssertionError(f"runtime v10 marker count={value.count(MARKER)}")
    for needle in (
        "function _crawlFollowable(url, fromUrl)",
        "if (_directMedia(url)) return true;",
        "rootOnly && next.origin !== from.origin",
        "_crawlFollowable(next,responseUrl)",
    ):
        if needle not in value:
            raise AssertionError(f"runtime v10 missing: {needle}")


def main() -> int:
    changed = patch()
    print(f"PROVIDER_BASE_RUNTIME_V10_OK changed={str(changed).lower()} external_bare_root_rejected=1 direct_media_preserved=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
