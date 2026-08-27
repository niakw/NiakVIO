#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Normalize provider runtime repository dependencies into durable local policy.

Runtime provider bundles may inherit GitHub-hosted JSON registries from upstreams.
Those links are maintenance inputs, not playback dependencies. Address discovery
(hub/Telegram/direct/search/LKG) owns ``official_site`` / ``official_api``;
provider rebuilds materialize those persisted terminal values into runtime bytes.

This normalizer also enforces ownership: domain-routing policy must not leak back
into the Core media-policy normalizer. The media layer owns identity/presentation,
not provider address discovery.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "provider-overrides.json"
CORE_MEDIA_POLICY = ROOT / "scripts" / "normalize_core_media_policy.py"
PATCH = "scripts/provider_patches/runtime_repository_domain_materializer_v1.py"
TVVVV_DOMAINS = "https://raw.githubusercontent.com/phisher98/TVVVV/refs/heads/main/domains.json"
SAPARIYANEEL_DOMAINS = (
    "https://raw.githubusercontent.com/sapariyaneel/nuvio-plugin/refs/heads/main/domains.json"
)
ZINK_REPOSITORY_DOMAINS = (
    "https://raw.githubusercontent.com/PirateZoro9/asura-providers/main/urls.json"
)

CINEBY_SITE = "https://www.cineby.at"
CINEBY_API = "https://api.speedracelight.com"
CINEBY_NOTE = (
    "Cineby runtime domain discovery is materialized from NiakVIO's persisted terminal/API; "
    "the upstream GitHub domains.json is maintenance-only and never fetched during playback."
)
CINEBY_OPTIONS = {
    "resolver_function": "getDomains",
    "materialized_value": {
        "cineby": {"$from": "official_site", "fallback": CINEBY_SITE},
        "speedracelight": {"$from": "official_api", "fallback": CINEBY_API},
    },
    "forbidden_urls": [SAPARIYANEEL_DOMAINS],
}

UHDMOVIES_SITE = "https://uhdmovies.autos"
UHDMOVIES_NOTE = (
    "UHDMovies runtime domain discovery is materialized from NiakVIO's persisted terminal; "
    "the TVVVV domains.json registry is maintenance-only and never fetched during playback."
)
UHDMOVIES_OPTIONS = {
    "resolver_function": "domainCandidates",
    "materialized_value": [{"$from": "official_site", "fallback": UHDMOVIES_SITE}],
    "forbidden_urls": [TVVVV_DOMAINS],
}

FOURKHDHUB_SITE = "https://new4.hdhub4u.cl"
FOURKHDHUB_NOTE = (
    "4KHDHub runtime domain discovery is materialized from NiakVIO's persisted terminal; "
    "the TVVVV domains.json registry is maintenance-only and never fetched during playback."
)
FOURKHDHUB_OPTIONS = {
    "resolver_function": "fetchLatestDomain",
    "materialized_value": {"$from": "official_site", "fallback": FOURKHDHUB_SITE},
    "forbidden_urls": [TVVVV_DOMAINS],
}

ZINK_SITE = "https://zinkmovies.wtf"
ZINK_NOTE = (
    "ZinkMovies address discovery is owned by provider-hubs.json and the resolver; the validated "
    "terminal is materialized into baseUrl and the upstream repository registry is never fetched at playback."
)
ZINK_OPTIONS = {
    "resolver_function": "refreshDomains",
    "mode": "assign",
    "assign_target": "baseUrl",
    "materialized_value": {"$from": "official_site", "fallback": ZINK_SITE},
    "forbidden_urls": [ZINK_REPOSITORY_DOMAINS],
}

GOATED_SITE = "https://goated.cx"
GOATED_API = "https://api.reallyfast.xyz"
GOATED_NOTE = (
    "Goated runtime API discovery is materialized from its provider fallback instead of fetching "
    "the upstream GitHub domains.json during playback."
)
GOATED_OPTIONS = {
    "resolver_function": "getDomains",
    "materialized_value": {"reallyfast": GOATED_API},
    "forbidden_urls": [SAPARIYANEEL_DOMAINS],
}


def load() -> dict[str, Any]:
    value = json.loads(CONFIG.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("provider-overrides.json must be an object")
    return value


def _notes(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    raise ValueError("provider notes must be a string or array")


def _valid_url(value: object) -> bool:
    return isinstance(value, str) and value.strip().startswith(("http://", "https://"))


def _ensure_materializer(
    providers: dict[str, Any],
    provider_id: str,
    *,
    options_value: dict[str, Any],
    note: str,
    default_site: str | None = None,
    default_api: str | None = None,
) -> list[str]:
    changed: list[str] = []
    raw_row = providers.get(provider_id)
    if raw_row is None:
        raw_row = {}
        providers[provider_id] = raw_row
        changed.append(f"provider_patches.{provider_id}")
    if not isinstance(raw_row, dict):
        raise ValueError(f"provider_patches.{provider_id} must be an object")
    row = raw_row

    scripts = row.get("patch_scripts") or []
    if not isinstance(scripts, list):
        raise ValueError(f"provider_patches.{provider_id}.patch_scripts must be an array")
    normalized_scripts = [str(path) for path in scripts if str(path).strip() and str(path) != PATCH]
    normalized_scripts.insert(0, PATCH)
    if normalized_scripts != scripts:
        row["patch_scripts"] = normalized_scripts
        changed.append(f"provider_patches.{provider_id}.patch_scripts")

    options = row.get("patch_script_options") or {}
    if not isinstance(options, dict):
        raise ValueError(f"provider_patches.{provider_id}.patch_script_options must be an object")
    if options.get(PATCH) != options_value:
        options[PATCH] = options_value
        row["patch_script_options"] = options
        changed.append(f"provider_patches.{provider_id}.patch_script_options")

    # Repository registry literals are never address replacements. A former Zink
    # one-shot incorrectly mapped one to a discovery hub; remove such mappings and
    # let the materializer own the provider-side resolver function instead.
    registry_urls = {str(url) for url in (options_value.get("forbidden_urls") or [])}
    for field in ("replacements", "route_replacements", "runtime_domain_replacements"):
        mapping = row.get(field)
        if mapping is None:
            continue
        if not isinstance(mapping, dict):
            raise ValueError(f"provider_patches.{provider_id}.{field} must be an object")
        cleaned = {str(key): value for key, value in mapping.items() if str(key) not in registry_urls}
        if cleaned != mapping:
            row[field] = cleaned
            changed.append(f"provider_patches.{provider_id}.{field}:remove_repository_registry")

    # Defaults bootstrap an offline/fresh checkout only. A route previously
    # validated and persisted by resolve_provider_hubs.py is never overwritten.
    if default_site is not None and not _valid_url(row.get("official_site")):
        row["official_site"] = default_site
        changed.append(f"provider_patches.{provider_id}.official_site:fallback")
    if default_api is not None and not _valid_url(row.get("official_api")):
        row["official_api"] = default_api
        changed.append(f"provider_patches.{provider_id}.official_api:fallback")

    notes = _notes(row.get("notes"))
    notes = [
        existing for existing in notes
        if not any(url in existing for url in registry_urls) or "maintenance-only" in existing.casefold()
    ]
    if note not in notes:
        notes.append(note)
    if notes != row.get("notes"):
        row["notes"] = notes
        changed.append(f"provider_patches.{provider_id}.notes")
    return changed


def _normalize_core_media_ownership(*, apply: bool) -> list[str]:
    """Remove the retired Zink address policy from the media normalizer.

    Keeping this as a guard prevents a future merge from making a media-policy
    normalizer rewrite provider routing again. It is intentionally exact/fail-
    closed: only the known retired blocks are removed.
    """
    source = CORE_MEDIA_POLICY.read_text(encoding="utf-8")
    normalized = source
    normalized = re.sub(
        r'ZINK_REPOSITORY_DOMAIN_SOURCE = \([\s\S]*?\nZINK_POLICY_NOTE = \([\s\S]*?\n\)\n\n',
        "",
        normalized,
        count=1,
    )
    normalized = re.sub(
        r'\ndef _normalize_zink_domain_discovery\([\s\S]*?(?=\ndef normalize\()',
        "\n",
        normalized,
        count=1,
    )
    normalized = normalized.replace("    _normalize_zink_domain_discovery(providers, changed)\n", "")
    normalized = re.sub(
        r'\n    zink = value\["provider_patches"\]\.get\("zinkmovies"\)[\s\S]*?(?=\n    runtime = ROOT /)',
        "\n",
        normalized,
        count=1,
    )
    changed: list[str] = []
    if normalized != source:
        changed.append("scripts/normalize_core_media_policy.py:remove_address_routing_ownership")
        if apply:
            CORE_MEDIA_POLICY.write_text(normalized, encoding="utf-8")
    forbidden = (
        "ZINK_REPOSITORY_DOMAIN_SOURCE",
        "_normalize_zink_domain_discovery",
        "repository domain lookup must materialize to the official hub",
    )
    check_source = normalized
    if any(token in check_source for token in forbidden):
        raise ValueError("Core media policy still owns provider address routing")
    return changed


def normalize(value: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    providers = value.get("provider_patches")
    if not isinstance(providers, dict):
        raise ValueError("provider_patches must be an object")
    changed: list[str] = []
    changed += _ensure_materializer(
        providers,
        "cineby",
        options_value=CINEBY_OPTIONS,
        note=CINEBY_NOTE,
        default_site=CINEBY_SITE,
        default_api=CINEBY_API,
    )
    changed += _ensure_materializer(
        providers,
        "uhdmovies",
        options_value=UHDMOVIES_OPTIONS,
        note=UHDMOVIES_NOTE,
        default_site=UHDMOVIES_SITE,
    )
    changed += _ensure_materializer(
        providers,
        "4khdhub",
        options_value=FOURKHDHUB_OPTIONS,
        note=FOURKHDHUB_NOTE,
        default_site=FOURKHDHUB_SITE,
    )
    changed += _ensure_materializer(
        providers,
        "zinkmovies",
        options_value=ZINK_OPTIONS,
        note=ZINK_NOTE,
        default_site=ZINK_SITE,
    )
    changed += _ensure_materializer(
        providers,
        "goated",
        options_value=GOATED_OPTIONS,
        note=GOATED_NOTE,
        default_site=GOATED_SITE,
    )
    return value, changed


def _assert_provider(
    providers: dict[str, Any],
    provider_id: str,
    *,
    expected_options: dict[str, Any],
    require_site: bool = False,
    require_api: bool = False,
) -> None:
    row = providers.get(provider_id)
    if not isinstance(row, dict):
        raise ValueError(f"provider_patches.{provider_id} must remain configured")
    scripts = [str(path) for path in (row.get("patch_scripts") or [])]
    if not scripts or scripts[0] != PATCH or scripts.count(PATCH) != 1:
        raise ValueError(f"{provider_id} runtime repository materializer must be the first unique provider patch")
    options = row.get("patch_script_options") or {}
    if not isinstance(options, dict) or options.get(PATCH) != expected_options:
        raise ValueError(f"{provider_id} runtime repository materializer options drifted")
    if require_site and not _valid_url(row.get("official_site")):
        raise ValueError(f"{provider_id} requires a persisted terminal site")
    if require_api and not _valid_url(row.get("official_api")):
        raise ValueError(f"{provider_id} requires a persisted terminal API")
    registry_urls = {str(url) for url in (expected_options.get("forbidden_urls") or [])}
    for field in ("replacements", "route_replacements", "runtime_domain_replacements"):
        mapping = row.get(field) or {}
        if not isinstance(mapping, dict):
            raise ValueError(f"provider_patches.{provider_id}.{field} must remain an object")
        overlap = registry_urls.intersection(str(key) for key in mapping)
        if overlap:
            raise ValueError(
                f"{provider_id} repository registry must not be used as an address replacement: {sorted(overlap)}"
            )


def assert_contract(value: dict[str, Any]) -> None:
    providers = value.get("provider_patches") or {}
    if not isinstance(providers, dict):
        raise ValueError("provider_patches must remain an object")
    _assert_provider(providers, "cineby", expected_options=CINEBY_OPTIONS, require_site=True, require_api=True)
    _assert_provider(providers, "uhdmovies", expected_options=UHDMOVIES_OPTIONS, require_site=True)
    _assert_provider(providers, "4khdhub", expected_options=FOURKHDHUB_OPTIONS, require_site=True)
    _assert_provider(providers, "zinkmovies", expected_options=ZINK_OPTIONS, require_site=True)
    _assert_provider(providers, "goated", expected_options=GOATED_OPTIONS, require_site=True)
    if not (ROOT / PATCH).is_file():
        raise ValueError("runtime repository domain materializer implementation is missing")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.apply == args.check:
        parser.error("choose exactly one of --apply or --check")

    value = load()
    normalized, changed = normalize(value)
    source_changes = _normalize_core_media_ownership(apply=args.apply)
    assert_contract(normalized)

    pending = list(changed) + list(source_changes)
    if args.check and pending:
        raise SystemExit("runtime repository dependency normalization required: " + ", ".join(pending))
    if args.apply and changed:
        CONFIG.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        "FIELD_RUNTIME_REPOSITORY_DEPENDENCIES "
        f"changed={len(pending)} cineby=resolved uhdmovies=resolved 4khdhub=resolved "
        "zinkmovies=resolved goated=resolved repository_runtime_fetches=0 address_owner=provider_resolver"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
