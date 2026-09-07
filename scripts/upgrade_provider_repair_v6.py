#!/usr/bin/env python3
"""Durable common repairs for proof-first provider portfolio recovery v6.

This migration contains only shared recognition/runtime behavior:
- classify colon-suffixed search endpoints (e.g. /1:search) as search;
- recognize search identity carried in URL or structured request body;
- build a direct API recipe when a proven reusable search request itself returned streams;
- apply the shared cumulative ProviderBase v10 crawl-budget fix.

Provider-specific URLs/methods/bodies remain DATA from live route proof.
"""
from __future__ import annotations

from pathlib import Path

import upgrade_provider_base_runtime_v10 as runtime_v10

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / "scripts" / "provider_route_proof.py"
RECOVERY = ROOT / "scripts" / "recover_provider_routes_from_upstreams.py"
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
    changed = False
    marker = "ROUTE_RECOVERY_TERMINAL_SEARCH_RECIPE_V6"
    if marker not in text:
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
        changed = True

    body_marker = "ROUTE_RECOVERY_BODY_SEARCH_RECIPE_V6"
    if body_marker not in text:
        helper_anchor = 'def build_simple_api_recipe(records: list[dict[str, Any]]) -> dict[str, Any] | None:\n'
        helper = '''# ROUTE_RECOVERY_BODY_SEARCH_RECIPE_V6
def _record_has_search_query(row: dict[str, Any]) -> bool:
    if "{query}" in str(row.get("route") or ""):
        return True
    spec = request_spec(row)
    if not isinstance(spec, dict):
        return False
    # Request specs are already sanitized/abstracted proof DATA. Searching the
    # serialized structure here only detects the canonical placeholder produced
    # by proof abstraction; it never recovers arbitrary provider code/data.
    return "{query}" in json.dumps(spec, ensure_ascii=False, sort_keys=True)


'''
        text = once(text, helper_anchor, helper + helper_anchor, "body-search-helper")
        old_search = '    searches = [row for row in records if row.get("role") == "search" and "{query}" in str(row.get("route"))]\n'
        new_search = '    searches = [row for row in records if row.get("role") == "search" and _record_has_search_query(row)]\n'
        text = once(text, old_search, new_search, "body-search-selection")
        changed = True

    if changed:
        RECOVERY.write_text(text, encoding="utf-8")
    return changed


def validate() -> None:
    proof = PROOF.read_text(encoding="utf-8")
    recovery = RECOVERY.read_text(encoding="utf-8")
    for needle in (
        MARKER,
        ':search(?:[/?#]|$)',
    ):
        if needle not in proof:
            raise AssertionError(f"proof v6 missing {needle}")
    for needle in (
        "ROUTE_RECOVERY_TERMINAL_SEARCH_RECIPE_V6",
        "ROUTE_RECOVERY_BODY_SEARCH_RECIPE_V6",
        'record["taskStreamCount"]',
        '_record_has_search_query(row)',
        'recipe["terminalSearchProof"] = True',
        'recipe["directRequest"] = spec',
    ):
        if needle not in recovery:
            raise AssertionError(f"recovery v6 missing {needle}")
    runtime_v10.validate()


def main() -> int:
    changed = patch_proof() | patch_recovery() | runtime_v10.patch()
    validate()
    print(f"PROVIDER_REPAIR_PORTFOLIO_V6_OK changed={str(bool(changed)).lower()} colon_search=1 body_search=1 terminal_post=1 provider_base_v10=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
