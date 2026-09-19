#!/usr/bin/env python3
"""Exclude Core/identity metadata transports from Provider HTTP evidence.

Provider route proof must describe the provider execution chain. Auxiliary identity
lookups (TMDB, IMDb->MAL mapping, Jikan metadata) can succeed while the provider
origin itself is blocked. Counting those successful helper requests as provider HTTP
prevents an otherwise 403/451-only provider traversal from being classified as
terminal-blocked and can also promote metadata routes as Provider DATA.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "validate_provider_v3_routes_live.py"
TEST = ROOT / "tests" / "provider_v3_live_route_validation_test.py"
MARKER = "PROVIDER_AUXILIARY_METADATA_FILTER_V1"

OLD_PROVIDER_FETCH = '''def provider_fetch(row: dict[str, Any]) -> bool:\n    url = str(row.get("final_url") or row.get("url") or "")\n    try:\n        host = (urllib.parse.urlsplit(url).hostname or "").casefold()\n    except ValueError:\n        host = ""\n    return host not in {"api.themoviedb.org", "www.themoviedb.org"}\n'''

NEW_PROVIDER_FETCH = '''# PROVIDER_AUXILIARY_METADATA_FILTER_V1\n# These origins provide Core/identity metadata used to resolve a title. They are\n# not Provider execution authority and must never validate, unblock, or create\n# Provider routes. In particular, a successful IMDb->MAL lookup must not mask a\n# 403-only traversal of the actual anime provider origin.\nNON_PROVIDER_METADATA_HOSTS = {\n    "api.themoviedb.org",\n    "www.themoviedb.org",\n    "id-mapping-api-malid.hf.space",\n    "api.jikan.moe",\n}\n\n\ndef provider_fetch(row: dict[str, Any]) -> bool:\n    url = str(row.get("final_url") or row.get("url") or "")\n    try:\n        host = (urllib.parse.urlsplit(url).hostname or "").casefold()\n    except ValueError:\n        host = ""\n    return host not in NON_PROVIDER_METADATA_HOSTS\n'''

OLD_TEST_IMPORT = '''from validate_provider_v3_routes_live import (  # noqa: E402\n    recipe_is_live,\n    route_matches_url,\n    validate_and_promote,\n)\n'''

NEW_TEST_IMPORT = '''from validate_provider_v3_routes_live import (  # noqa: E402\n    provider_fetch,\n    recipe_is_live,\n    route_matches_url,\n    validate_and_promote,\n)\n'''

TEST_BLOCK = '''\n# Auxiliary metadata/identity calls are not Provider HTTP evidence. A 200 from\n# IMDb->MAL or Jikan must not mask an actual provider-origin 403/451 block.\nassert not provider_fetch({"url": "https://api.themoviedb.org/3/tv/1/external_ids"})\nassert not provider_fetch({"url": "https://id-mapping-api-malid.hf.space/api/resolve?id=tt1234567&s=1&e=1"})\nassert not provider_fetch({"url": "https://api.jikan.moe/v4/anime/1"})\nassert provider_fetch({"url": "https://anizone.to/anime?search=Failure%20Frame"})\n'''


def patch() -> bool:
    changed = False

    target = TARGET.read_text(encoding="utf-8")
    if MARKER not in target:
        count = target.count(OLD_PROVIDER_FETCH)
        if count != 1:
            raise AssertionError(f"provider_fetch anchor count={count}")
        target = target.replace(OLD_PROVIDER_FETCH, NEW_PROVIDER_FETCH, 1)
        TARGET.write_text(target, encoding="utf-8")
        changed = True

    test = TEST.read_text(encoding="utf-8")
    if "id-mapping-api-malid.hf.space/api/resolve" not in test:
        count = test.count(OLD_TEST_IMPORT)
        if count != 1:
            raise AssertionError(f"live-route test import anchor count={count}")
        test = test.replace(OLD_TEST_IMPORT, NEW_TEST_IMPORT, 1)
        insert_at = test.index("\n\nassert route_matches_url(")
        test = test[:insert_at] + TEST_BLOCK + test[insert_at:]
        TEST.write_text(test, encoding="utf-8")
        changed = True

    validate()
    return changed


def validate() -> None:
    target = TARGET.read_text(encoding="utf-8")
    test = TEST.read_text(encoding="utf-8")
    required_hosts = (
        "api.themoviedb.org",
        "www.themoviedb.org",
        "id-mapping-api-malid.hf.space",
        "api.jikan.moe",
    )
    if MARKER not in target:
        raise AssertionError("auxiliary metadata filter marker missing")
    for host in required_hosts:
        if host not in target:
            raise AssertionError(f"non-provider metadata host missing: {host}")
    if "return host not in NON_PROVIDER_METADATA_HOSTS" not in target:
        raise AssertionError("provider_fetch does not use metadata host filter")
    if "assert provider_fetch({\"url\": \"https://anizone.to/anime?search=Failure%20Frame\"})" not in test:
        raise AssertionError("provider-origin positive control missing")
    if "assert not provider_fetch({\"url\": \"https://id-mapping-api-malid.hf.space/api/resolve" not in test:
        raise AssertionError("identity-helper negative control missing")


def main() -> int:
    changed = patch()
    print(
        "PROVIDER_AUXILIARY_METADATA_FILTER_V1_OK "
        f"changed={str(changed).lower()} core_metadata_is_provider_evidence=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
