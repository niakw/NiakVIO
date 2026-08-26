#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Normalize provider runtime repository dependencies into durable local policy.

Runtime provider bundles may inherit GitHub-hosted JSON registries from upstreams.
Those links are maintenance inputs, not playback dependencies. This normalizer
persists reusable patch configuration so every future reapply/sync materializes
reviewed endpoints before publication.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "provider-overrides.json"
PATCH = "scripts/provider_patches/runtime_repository_domain_materializer_v1.py"
TVVVV_DOMAINS = "https://raw.githubusercontent.com/phisher98/TVVVV/refs/heads/main/domains.json"

CINEBY_REPOSITORY_DOMAINS = (
    "https://raw.githubusercontent.com/sapariyaneel/nuvio-plugin/refs/heads/main/domains.json"
)
CINEBY_SITE = "https://www.cineby.at"
CINEBY_API = "https://api.speedracelight.com"
CINEBY_NOTE = (
    "Cineby runtime domain discovery is materialized from reviewed maintenance data; "
    "the upstream GitHub domains.json is maintenance-only and never fetched during playback."
)
CINEBY_OPTIONS = {
    "resolver_function": "getDomains",
    "materialized_value": {
        "cineby": CINEBY_SITE,
        "speedracelight": CINEBY_API,
    },
    "forbidden_urls": [CINEBY_REPOSITORY_DOMAINS],
}

UHDMOVIES_SITE = "https://uhdmovies.autos"
UHDMOVIES_NOTE = (
    "UHDMovies runtime domain discovery is materialized from the reviewed terminal; "
    "the TVVVV domains.json registry is maintenance-only and never fetched during playback."
)
UHDMOVIES_OPTIONS = {
    "resolver_function": "domainCandidates",
    "materialized_value": [UHDMOVIES_SITE],
    "forbidden_urls": [TVVVV_DOMAINS],
}

FOURKHDHUB_SITE = "https://new4.hdhub4u.cl"
FOURKHDHUB_NOTE = (
    "4KHDHub runtime domain discovery is materialized from NiakVIO's reviewed terminal; "
    "the TVVVV domains.json registry is maintenance-only and never fetched during playback."
)
FOURKHDHUB_OPTIONS = {
    "resolver_function": "fetchLatestDomain",
    "materialized_value": FOURKHDHUB_SITE,
    "forbidden_urls": [TVVVV_DOMAINS],
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


def _ensure_materializer(
    providers: dict[str, Any],
    provider_id: str,
    *,
    options_value: dict[str, Any],
    note: str,
    official_site: str | None = None,
    official_api: str | None = None,
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
    normalized_scripts = [str(path) for path in scripts if str(path).strip()]
    if PATCH not in normalized_scripts:
        normalized_scripts.append(PATCH)
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

    if official_site is not None and row.get("official_site") != official_site:
        row["official_site"] = official_site
        changed.append(f"provider_patches.{provider_id}.official_site")
    if official_api is not None and row.get("official_api") != official_api:
        row["official_api"] = official_api
        changed.append(f"provider_patches.{provider_id}.official_api")

    notes = _notes(row.get("notes"))
    registry_urls = set(str(url) for url in (options_value.get("forbidden_urls") or []))
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
        official_site=CINEBY_SITE,
        official_api=CINEBY_API,
    )
    changed += _ensure_materializer(
        providers,
        "uhdmovies",
        options_value=UHDMOVIES_OPTIONS,
        note=UHDMOVIES_NOTE,
        official_site=UHDMOVIES_SITE,
    )
    changed += _ensure_materializer(
        providers,
        "4khdhub",
        options_value=FOURKHDHUB_OPTIONS,
        note=FOURKHDHUB_NOTE,
        official_site=FOURKHDHUB_SITE,
    )
    return value, changed


def _assert_provider(
    providers: dict[str, Any],
    provider_id: str,
    *,
    expected_options: dict[str, Any],
    official_site: str | None = None,
    official_api: str | None = None,
) -> None:
    row = providers.get(provider_id)
    if not isinstance(row, dict):
        raise ValueError(f"provider_patches.{provider_id} must remain configured")
    scripts = [str(path) for path in (row.get("patch_scripts") or [])]
    if PATCH not in scripts:
        raise ValueError(f"{provider_id} runtime repository materializer is missing")
    options = row.get("patch_script_options") or {}
    if not isinstance(options, dict) or options.get(PATCH) != expected_options:
        raise ValueError(f"{provider_id} runtime repository materializer options drifted")
    if official_site is not None and row.get("official_site") != official_site:
        raise ValueError(f"{provider_id} reviewed site endpoint drifted")
    if official_api is not None and row.get("official_api") != official_api:
        raise ValueError(f"{provider_id} reviewed API endpoint drifted")


def assert_contract(value: dict[str, Any]) -> None:
    providers = value.get("provider_patches") or {}
    if not isinstance(providers, dict):
        raise ValueError("provider_patches must remain an object")
    _assert_provider(
        providers,
        "cineby",
        expected_options=CINEBY_OPTIONS,
        official_site=CINEBY_SITE,
        official_api=CINEBY_API,
    )
    _assert_provider(
        providers,
        "uhdmovies",
        expected_options=UHDMOVIES_OPTIONS,
        official_site=UHDMOVIES_SITE,
    )
    _assert_provider(
        providers,
        "4khdhub",
        expected_options=FOURKHDHUB_OPTIONS,
        official_site=FOURKHDHUB_SITE,
    )
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
    assert_contract(normalized)

    if args.check and changed:
        raise SystemExit("runtime repository dependency normalization required: " + ", ".join(changed))
    if args.apply and changed:
        CONFIG.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        "FIELD_RUNTIME_REPOSITORY_DEPENDENCIES "
        f"changed={len(changed)} cineby=materialized uhdmovies=materialized "
        "4khdhub=materialized repository_runtime_fetches=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
