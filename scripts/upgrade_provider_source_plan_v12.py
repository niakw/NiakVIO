#!/usr/bin/env python3
"""Source Plan V12: exact catalogue identity ranking + bounded file resolver crawl.

Live V12 page diagnostics exposed two generic losses:
- catalogue search pages can contain many URLs that all include the requested title;
  the common score needs to prefer the candidate with the least unexplained suffix
  instead of treating sequel/special/spin-off URLs nearly equally;
- a provider detail page may expose an explicit external resolver as `/file/<id>`.
  The bounded crawler already treats watch/embed/download pages as intermediate
  resolvers, but `/file/` was excluded before it could be fetched.

This migration is provider-agnostic. `/file/` remains an intermediate crawl shape:
`_directMedia()` must still prove the final media URL before output.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_SOURCE_PLAN_V12"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_base() -> bool:
    text = BASE.read_text(encoding="utf-8")
    if MARKER in text:
        validate_base(text)
        return False
    if "NIAKVIO_PROVIDER_SOURCE_PLAN_V10" not in text:
        raise AssertionError("Source Plan V12 requires V10 first")

    # Prefer the URL whose final path component most closely matches the title.
    # Generic transport suffixes (tv/series/show/anime) do not count as unexplained
    # content tokens; every other extra token reduces the bonus substantially.
    text = once(
        text,
        '''  if (slug && path.includes(slug)) score += 120;\n  for (const token of tokens) if (path.includes(token)) score += 18;\n''',
        '''  if (slug && path.includes(slug)) score += 120;\n  // NIAKVIO_PROVIDER_SOURCE_PLAN_V12\n  if (slug) {\n    const leaf = path.split("/").filter(Boolean).pop() || "";\n    const titleTokens = slug.split("-").filter(Boolean);\n    const leafTokens = leaf.split(/[^a-z0-9]+/).filter(Boolean);\n    const titleSet = new Set(titleTokens);\n    const missing = titleTokens.filter(token => !leafTokens.includes(token));\n    if (!missing.length) {\n      const extras = leafTokens.filter(token =>\n        !titleSet.has(token) &&\n        !["tv", "series", "show", "anime"].includes(token) &&\n        !/^\\d{4}$/.test(token)\n      );\n      score += Math.max(-120, 240 - extras.length * 60);\n    }\n  }\n  for (const token of tokens) if (path.includes(token)) score += 18;\n''',
        "candidate-exact-title-distance",
    )

    # Media-shape conflicts are a strong generic negative signal. This is not an
    # identity rejection: it only changes ordering among already-discovered links.
    text = once(
        text,
        '''function _spv4UrlScore(url, meta, mediaType, season) {\n  let score = _candidateScore(url, meta) + _spv10SeasonUrlScore(url, mediaType, season);\n''',
        '''function _spv4UrlScore(url, meta, mediaType, season) {\n  let score = _candidateScore(url, meta) + _spv10SeasonUrlScore(url, mediaType, season);\n  try {\n    const path = decodeURIComponent(new URL(url).pathname || "").toLowerCase();\n    if (mediaType !== "movie" && /(?:^|[-_/])(?:movie|film|specials?|ova|ona)(?:[-_/]|$)/i.test(path)) score -= 220;\n    if (mediaType === "movie" && /(?:season|saison)[-_ /]*\\d{1,3}|(?:^|[-_/])s\\d{1,3}(?:[-_/]|$)/i.test(path)) score -= 220;\n  } catch (_) {}\n''',
        "catalogue-media-shape-ranking",
    )

    # `/file/<id>` is a common resolver-page shape. It is only crawl-eligible;
    # final media still has to satisfy `_directMedia()` / media content-type proof.
    text = once(
        text,
        '''    return /\\/(?:watch|embed|player|play|video|videos|stream|streams|source|sources|server|servers|resolve|proxy|drive|download)(?:[/?#.-]|$)/i.test(parsed.pathname + parsed.search);\n''',
        '''    return /\\/(?:watch|embed|player|play|video|videos|stream|streams|source|sources|server|servers|resolve|proxy|drive|download|file|files)(?:[/?#.-]|$)/i.test(parsed.pathname + parsed.search);\n''',
        "player-like-file-resolver",
    )
    text = once(
        text,
        '''    if (/\\/(?:watch|embed|player|play|video|stream|source|server|resolve|proxy|drive|download|dl|links?|redirect)(?:[/?#.-]|$)/i.test(path)) score += 420;\n''',
        '''    if (/\\/(?:watch|embed|player|play|video|stream|source|server|resolve|proxy|drive|download|file|files|dl|links?|redirect)(?:[/?#.-]|$)/i.test(path)) score += 420;\n''',
        "crawl-score-file-resolver",
    )

    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return True


def validate_base(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    for needle in (
        MARKER,
        "240 - extras.length * 60",
        '!["tv", "series", "show", "anime"].includes(token)',
        "movie|film|specials?|ova|ona",
        "download|file|files",
        "redirect)(?:[/?#.-]|$)/i.test(path)",
    ):
        if needle not in value:
            raise AssertionError(f"V12 ProviderBase missing: {needle}")


def main() -> int:
    changed = patch_base()
    print(
        f"PROVIDER_SOURCE_PLAN_V12_OK changed={str(changed).lower()} "
        "exact_title_distance=1 media_shape_ranking=1 file_resolver_crawl=1 "
        "direct_media_proof_required=1 provider_specific_hosts=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
