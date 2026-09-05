#!/usr/bin/env python3
"""Make Provider v3 route evidence redirect-aware without promoting redirects to DATA.

A provider route is the URL that NiakVIO requested. `final_url` is response/traversal
context after redirects. Both are evidence, but a redirect must never make the
original stable route look unexecuted and therefore eligible for destructive pruning.
`officialHub` is canonical provider authority too and must participate in the
contract-host gate.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "validate_provider_v3_routes_sequential.py"
MARKER = "PROVIDER_V3_REDIRECT_ROUTE_MATCH_V1"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one exact anchor, got {count}")
    return text.replace(old, new, 1)


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    original = text

    if MARKER not in text:
        helper_anchor = '''    return False\n\n\ndef _provider_contract_hosts(model: dict[str, Any]) -> set[str]:\n'''
        helper_replacement = '''    return False\n\n\n# PROVIDER_V3_REDIRECT_ROUTE_MATCH_V1\ndef _fetch_route_urls(fetch: dict[str, Any]) -> list[str]:\n    \"\"\"Request URL first; redirect target second. Both are evidence, not authority.\"\"\"\n    values: list[str] = []\n    for key in (\"url\", \"final_url\"):\n        raw = str(fetch.get(key) or \"\").strip()\n        if raw and raw not in values:\n            values.append(raw)\n    return values\n\n\ndef _fetch_matches_model_route(route: str, fetch: dict[str, Any], model: dict[str, Any]) -> bool:\n    return any(_route_matches_model_url(route, raw, model) for raw in _fetch_route_urls(fetch))\n\n\ndef _provider_contract_hosts(model: dict[str, Any]) -> set[str]:\n'''
        text = once(text, helper_anchor, helper_replacement, "redirect-aware-route-helper")

        old_host = '''def _fetch_on_contract_host(fetch: dict[str, Any], hosts: set[str]) -> bool:\n    if not hosts:\n        return True\n    raw = str(fetch.get(\"final_url\") or fetch.get(\"url\") or \"\")\n    try:\n        host = (urllib.parse.urlsplit(raw).hostname or \"\").casefold()\n    except ValueError:\n        return False\n    return host in hosts\n'''
        new_host = '''def _fetch_on_contract_host(fetch: dict[str, Any], hosts: set[str]) -> bool:\n    if not hosts:\n        return True\n    for raw in _fetch_route_urls(fetch):\n        try:\n            host = (urllib.parse.urlsplit(raw).hostname or \"\").casefold()\n        except ValueError:\n            continue\n        if host in hosts:\n            return True\n    return False\n'''
        text = once(text, old_host, new_host, "redirect-aware-contract-host")

        old_candidate_match = '''        for index, (fetch, task) in enumerate(fetch_rows):\n            actual = str(fetch.get(\"final_url\") or fetch.get(\"url\") or \"\")\n            if route and _route_matches_model_url(route, actual, model):\n                matches.append((fetch, task, index))\n                matched_indexes.add(index)\n'''
        new_candidate_match = '''        for index, (fetch, task) in enumerate(fetch_rows):\n            if route and _fetch_matches_model_route(route, fetch, model):\n                matches.append((fetch, task, index))\n                matched_indexes.add(index)\n'''
        text = once(text, old_candidate_match, new_candidate_match, "candidate-request-url-match")

        old_type_match = '''                    actual = str(fetch.get(\"final_url\") or fetch.get(\"url\") or \"\")\n                    if _route_matches_model_url(template, actual, model):\n                        evidence_by_type[media_type].append({\n'''
        new_type_match = '''                    if _fetch_matches_model_route(template, fetch, model):\n                        evidence_by_type[media_type].append({\n'''
        text = once(text, old_type_match, new_type_match, "declared-type-request-url-match")

    # This is part of the same redirect/authority contract. Keep it independently
    # idempotent so repositories that already carry V1 still receive officialHub.
    old_hosts = 'for key in ("knownSite", "officialSite", "officialApi", "fixedApi"):'
    new_hosts = 'for key in ("knownSite", "officialSite", "officialHub", "officialApi", "fixedApi"):'
    if old_hosts in text:
        text = text.replace(old_hosts, new_hosts, 1)
    elif new_hosts not in text:
        raise AssertionError("official-hub-contract-host: host tuple anchor missing")

    if text != original:
        TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return text != original


def validate(text: str) -> None:
    required = (
        MARKER,
        'for key in ("url", "final_url"):',
        'def _fetch_matches_model_route(',
        'if route and _fetch_matches_model_route(route, fetch, model):',
        'if _fetch_matches_model_route(template, fetch, model):',
        'for raw in _fetch_route_urls(fetch):',
        'for key in ("knownSite", "officialSite", "officialHub", "officialApi", "fixedApi"):',
    )
    for needle in required:
        if needle not in text:
            raise AssertionError(f"redirect route match missing: {needle}")
    forbidden = (
        'actual = str(fetch.get("final_url") or fetch.get("url") or "")\n            if route and _route_matches_model_url(route, actual, model):',
        'raw = str(fetch.get("final_url") or fetch.get("url") or "")\n    try:\n        host =',
        'for key in ("knownSite", "officialSite", "officialApi", "fixedApi"):',
    )
    for needle in forbidden:
        if needle in text:
            raise AssertionError(f"redirect route match retained stale rule: {needle}")


def main() -> int:
    changed = patch()
    print(
        "PROVIDER_V3_REDIRECT_ROUTE_MATCH_V1_OK "
        f"changed={str(changed).lower()} request_url=route_identity "
        "final_url=redirect_evidence official_hub=contract_authority"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
