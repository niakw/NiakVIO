#!/usr/bin/env python3
"""Durable common repairs for proof-first provider portfolio recovery v6.

This migration contains only shared recognition/runtime behavior:
- classify colon-suffixed search endpoints (e.g. /1:search) as search;
- build a direct API recipe when a proven reusable search request itself returned streams;
- avoid spending the provider deadline crawling an unrelated external origin root.

Provider-specific URLs/methods/bodies remain DATA from live route proof.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / "scripts" / "provider_route_proof.py"
RECOVERY = ROOT / "scripts" / "recover_provider_routes_from_upstreams.py"
BASE = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_REPAIR_PORTFOLIO_V6"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_proof() -> bool:
    text = PROOF.read_text(encoding="utf-8")
    if MARKER in text:
        return False
    old = 're.search(r"/(?:search|recherche)(?:[/?#]|$)", value)'
    new = 're.search(r"(?:/(?:search|recherche)(?:[/?#]|$)|:search(?:[/?#]|$))", value)'
    text = once(text, old, new, "colon-search-role")
    text = text.replace(
        "def route_role(route: str) -> str:\n",
        f"# {MARKER}\ndef route_role(route: str) -> str:\n",
        1,
    )
    PROOF.write_text(text, encoding="utf-8")
    return True


def patch_recovery() -> bool:
    text = RECOVERY.read_text(encoding="utf-8")
    marker = "ROUTE_RECOVERY_TERMINAL_SEARCH_RECIPE_V6"
    if marker in text:
        return False

    old_call = '''                record = route_record(item, semantic_type, fixture["slug"], source_meta)
                if record:
                    records.append(record)
                    task_records.append(record)
'''
    new_call = '''                record = route_record(item, semantic_type, fixture["slug"], source_meta)
                if record:
                    record["taskStreamCount"] = int(result.get("streams") or 0)
                    record["taskRawStreamCount"] = int(result.get("rawStreams") or 0)
                    records.append(record)
                    task_records.append(record)
'''
    text = once(text, old_call, new_call, "task-positive-route-evidence")

    old_return_guard = '''    route_keys = {"searchRoute", "movieRoute", "episodeRoute", "directRoute"}
    if not route_keys.intersection(recipe):
        return None
    if "searchRoute" in recipe and not ({"movieRoute", "episodeRoute"} & recipe.keys()):
        return None
    return recipe
'''
    new_return_guard = '''    # ROUTE_RECOVERY_TERMINAL_SEARCH_RECIPE_V6
    # Some APIs return playable/source URLs directly from their search POST.
    # When that exact reusable request produced streams in the upstream runtime,
    # replay it as a direct route instead of discarding the proof because there
    # is no separate detail/movie/episode hop.
    if "searchRoute" in recipe and not ({"movieRoute", "episodeRoute"} & recipe.keys()):
        terminal = next((row for row in searches if int(row.get("taskStreamCount") or 0) > 0), None)
        if terminal is not None:
            recipe.pop("searchRoute", None)
            recipe.pop("searchRequest", None)
            recipe["directRoute"] = as_recipe_route(terminal, base)
            spec = request_spec(terminal)
            if spec:
                recipe["directRequest"] = spec
            recipe["terminalSearchProof"] = True
    route_keys = {"searchRoute", "movieRoute", "episodeRoute", "directRoute"}
    if not route_keys.intersection(recipe):
        return None
    if "searchRoute" in recipe and not ({"movieRoute", "episodeRoute"} & recipe.keys()):
        return None
    return recipe
'''
    text = once(text, old_return_guard, new_return_guard, "terminal-search-direct-recipe")
    RECOVERY.write_text(text, encoding="utf-8")
    return True


def patch_base() -> bool:
    text = BASE.read_text(encoding="utf-8")
    marker = "NIAKVIO_PROVIDER_BASE_BOUNDED_EXTERNAL_ROOT_V10"
    if marker in text:
        return False

    pattern = re.compile(r'(function _crawlEligible\(url\) \{.*?\n\})\n(function _crawlUrlScore\(url\) \{)', re.S)
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise AssertionError(f"crawl helper insertion anchors={len(matches)}")
    helper = r'''
/* NIAKVIO_PROVIDER_BASE_BOUNDED_EXTERNAL_ROOT_V10 */
function _crawlFollowable(url, fromUrl) {
  if (!_crawlEligible(url)) return false;
  if (_directMedia(url)) return true;
  try {
    const next = new URL(url);
    const from = new URL(fromUrl);
    const rootOnly = (next.pathname === "/" || next.pathname === "") && !next.search && !next.hash;
    // A bare external origin is normally a landing/decorative link, not a
    // provider resolver. Following it can consume the entire provider deadline
    // (observed with HubCloud) and discard already-discovered streams.
    if (rootOnly && next.origin !== from.origin) return false;
    return true;
  } catch (_) { return false; }
}
'''
    match = matches[0]
    replacement = match.group(1) + "\n" + helper + match.group(2)
    text = text[:match.start()] + replacement + text[match.end():]

    old = '_uniq(urls.map(_crawlCanonical)).filter(Boolean).filter(_crawlEligible).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a))'
    new = '_uniq(urls.map(_crawlCanonical)).filter(Boolean).filter(next=>_crawlFollowable(next,responseUrl)).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a))'
    text = once(text, old, new, "bounded-external-root-crawl")
    BASE.write_text(text, encoding="utf-8")
    return True


def validate() -> None:
    proof = PROOF.read_text(encoding="utf-8")
    recovery = RECOVERY.read_text(encoding="utf-8")
    base = BASE.read_text(encoding="utf-8")
    for needle in (
        MARKER,
        ':search(?:[/?#]|$)',
    ):
        if needle not in proof:
            raise AssertionError(f"proof v6 missing {needle}")
    for needle in (
        "ROUTE_RECOVERY_TERMINAL_SEARCH_RECIPE_V6",
        'record["taskStreamCount"]',
        'recipe["terminalSearchProof"] = True',
        'recipe["directRequest"] = spec',
    ):
        if needle not in recovery:
            raise AssertionError(f"recovery v6 missing {needle}")
    for needle in (
        "NIAKVIO_PROVIDER_BASE_BOUNDED_EXTERNAL_ROOT_V10",
        "function _crawlFollowable(url, fromUrl)",
        "rootOnly && next.origin !== from.origin",
        "_crawlFollowable(next,responseUrl)",
    ):
        if needle not in base:
            raise AssertionError(f"ProviderBase v10 missing {needle}")


def main() -> int:
    changed = patch_proof() | patch_recovery() | patch_base()
    validate()
    print(f"PROVIDER_REPAIR_PORTFOLIO_V6_OK changed={str(bool(changed)).lower()} colon_search=1 terminal_post=1 external_root_guard=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
