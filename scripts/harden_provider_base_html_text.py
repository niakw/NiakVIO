#!/usr/bin/env python3
"""Remove unsafe regex-based HTML stripping from the canonical ProviderBase source.

The common ProviderBase already owns ``_htmlVisibleText``: a deterministic scanner
used specifically to avoid CodeQL's bad-HTML-filtering-regexp class. Older source
plan/runtime migrations can leave one of two historical ``<[^>]+>`` label
normalizers behind. This hardening pass is deliberately narrow: it rewrites only
those known label-scoring forms, then fails closed if any matching unsafe HTML
filter remains in the generated ProviderBase source.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_base_store.py"

V14_CHAIN = '''_text(match[4])
      .replace(/<[^>]+>/g, " ")
      .replace(/&nbsp;/gi, " ")
      .replace(/&amp;/gi, "&")
      .replace(/\\s+/g, " ")
      .trim()'''
V7_INLINE = '_text(match[4]).replace(/<[^>]+>/g, " ")'
SAFE = '_htmlVisibleText(match[4])'
FORBIDDEN = '.replace(/<[^>]+>/g'


def patch() -> int:
    text = TARGET.read_text(encoding="utf-8")
    if "function _htmlVisibleText(value)" not in text:
        raise AssertionError("ProviderBase is missing the deterministic HTML text scanner")

    changed = 0
    v14_count = text.count(V14_CHAIN)
    if v14_count:
        text = text.replace(V14_CHAIN, SAFE)
        changed += v14_count

    v7_count = text.count(V7_INLINE)
    if v7_count:
        text = text.replace(V7_INLINE, SAFE)
        changed += v7_count

    if FORBIDDEN in text:
        raise AssertionError("ProviderBase still contains an unsafe HTML filtering regexp")

    TARGET.write_text(text, encoding="utf-8")
    return changed


def main() -> int:
    changed = patch()
    check = TARGET.read_text(encoding="utf-8")
    if FORBIDDEN in check:
        raise AssertionError("ProviderBase HTML regex hardening did not converge")
    if SAFE not in check:
        raise AssertionError("ProviderBase HTML hardening has no safe scanner call")
    print(f"PROVIDER_BASE_HTML_TEXT_HARDENING_OK changed={changed} unsafe_html_filter_regex=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
