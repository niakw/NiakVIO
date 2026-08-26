#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Normalize provider runtime repository dependencies into durable local policy.

Runtime provider bundles may inherit GitHub-hosted JSON registries from upstreams.
Those links are maintenance inputs, not playback dependencies. This normalizer
persists a reusable patch configuration so every future reapply/sync materializes
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
    "values": {
        "cineby": CINEBY_SITE,
        "speedracelight": CINEBY_API,
    },
    "forbidden_urls": [CINEBY_REPOSITORY_DOMAINS],
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


def normalize(value: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    changed: list[str] = []
    providers = value.get("provider_patches")
    if not isinstance(providers, dict):
        raise ValueError("provider_patches must be an object")

    row = providers.get("cineby")
    if not isinstance(row, dict):
        raise ValueError("provider_patches.cineby must be an object")

    scripts = row.get("patch_scripts") or []
    if not isinstance(scripts, list):
        raise ValueError("provider_patches.cineby.patch_scripts must be an array")
    normalized_scripts = [str(path) for path in scripts if str(path).strip()]
    if PATCH not in normalized_scripts:
        normalized_scripts.append(PATCH)
    if normalized_scripts != scripts:
        row["patch_scripts"] = normalized_scripts
        changed.append("provider_patches.cineby.patch_scripts")

    options = row.get("patch_script_options") or {}
    if not isinstance(options, dict):
        raise ValueError("provider_patches.cineby.patch_script_options must be an object")
    if options.get(PATCH) != CINEBY_OPTIONS:
        options[PATCH] = CINEBY_OPTIONS
        row["patch_script_options"] = options
        changed.append("provider_patches.cineby.patch_script_options")

    if row.get("official_site") != CINEBY_SITE:
        row["official_site"] = CINEBY_SITE
        changed.append("provider_patches.cineby.official_site")
    if row.get("official_api") != CINEBY_API:
        row["official_api"] = CINEBY_API
        changed.append("provider_patches.cineby.official_api")

    notes = _notes(row.get("notes"))
    notes = [
        note for note in notes
        if CINEBY_REPOSITORY_DOMAINS not in note or "maintenance-only" in note.casefold()
    ]
    if CINEBY_NOTE not in notes:
        notes.append(CINEBY_NOTE)
    if notes != row.get("notes"):
        row["notes"] = notes
        changed.append("provider_patches.cineby.notes")

    return value, changed


def assert_contract(value: dict[str, Any]) -> None:
    providers = value.get("provider_patches") or {}
    row = providers.get("cineby")
    if not isinstance(row, dict):
        raise ValueError("provider_patches.cineby must remain configured")
    scripts = [str(path) for path in (row.get("patch_scripts") or [])]
    if PATCH not in scripts:
        raise ValueError("Cineby runtime repository materializer is missing")
    options = row.get("patch_script_options") or {}
    if not isinstance(options, dict) or options.get(PATCH) != CINEBY_OPTIONS:
        raise ValueError("Cineby runtime repository materializer options drifted")
    if row.get("official_site") != CINEBY_SITE or row.get("official_api") != CINEBY_API:
        raise ValueError("Cineby reviewed site/API endpoints drifted")
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
        f"changed={len(changed)} cineby=materialized repository_runtime_fetches=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
