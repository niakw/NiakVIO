#!/usr/bin/env python3
"""Idempotently wire clean-v3 route Lego for surviving providers in the old #9-#18 batch.

This migration predates the current 46-provider scope. Historical providers that
have been removed from ``provider-overrides.json`` are archive knowledge and must
not make current repair fail. The migration also follows the current semantic
contract: AniKotoTV is canonical anime-only; ``tv`` may be a transport alias, but
``movie`` must never be manufactured.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"

DESIFLIX = "scripts/provider_patches/desiflix_runtime_v1.py"
ALLMOVIELAND = "scripts/provider_patches/allmovieland_runtime_v1.py"
ANIKOTOTV = "scripts/provider_patches/anikototv_runtime_v1.py"


def _load() -> dict[str, Any]:
    value = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError("provider-overrides.json must be an object")
    patches = value.get("provider_patches")
    if not isinstance(patches, dict):
        raise AssertionError("provider-overrides.json missing provider_patches")
    return value


def _required_row(patches: dict[str, Any], provider_id: str) -> dict[str, Any]:
    row = patches.get(provider_id)
    if not isinstance(row, dict):
        raise AssertionError(f"missing current provider patch row: {provider_id}")
    return row


def _optional_row(patches: dict[str, Any], provider_id: str) -> dict[str, Any] | None:
    row = patches.get(provider_id)
    return row if isinstance(row, dict) else None


def _set_legos(row: dict[str, Any], script: str, options: dict[str, Any]) -> None:
    scripts = [str(v) for v in row.get("provider_lego_scripts") or [] if str(v).strip()]
    if script not in scripts:
        scripts.append(script)
    row["provider_lego_scripts"] = scripts
    lego_options = row.get("provider_lego_options")
    if not isinstance(lego_options, dict):
        lego_options = {}
    lego_options[script] = options
    row["provider_lego_options"] = lego_options


def patch() -> bool:
    value = _load()
    patches = value["provider_patches"]
    before = json.dumps(value, ensure_ascii=False, sort_keys=True)

    desiflix = _required_row(patches, "desiflix")
    desiflix["published_types"] = ["movie", "tv"]
    desiflix["learned_routes"] = [
        "/stream/movie/{id}.json",
        "/stream/series/{id}:{season}:{episode}.json",
    ]
    # Live CI evidence on 2026-09-12: the declared manifest host still
    # answers but its IMDb routes intermittently stall, while the Worker
    # mirror returns the same current addon catalogue promptly.
    _set_legos(
        desiflix,
        DESIFLIX,
        {
            "base": "https://desiflix.stremioaddon.workers.dev",
            "fallbackBases": ["https://manifest.desitvhub.eu.org"],
        },
    )

    # allmovieland belonged to the historical 96-provider portfolio. If it is
    # still present in a migration fixture, keep the old migration idempotent;
    # if it has been removed from current overrides, skip it completely.
    allmovieland = _optional_row(patches, "allmovieland")
    if allmovieland is not None:
        allmovieland["published_types"] = ["movie", "tv"]
        allmovieland["learned_routes"] = [
            "/index.php?story={query}&do=search&subaction=search",
            "/play/{id}",
            "/playlist/{id}.txt",
        ]
        _set_legos(
            allmovieland,
            ALLMOVIELAND,
            {
                "sites": [
                    "https://allmovieland.to",
                    "https://allmovieland.art",
                    "https://allmovieland.one",
                    "https://allmovieland.io",
                ]
            },
        )

    anikoto = _required_row(patches, "anikototv")
    anikoto["published_types"] = ["anime"]
    # The public AniKotoAPI project documents these as the native site routes
    # it wraps internally. These routes are valid for anime identity/playback;
    # they do not imply a canonical movie lane.
    anikoto["learned_routes"] = [
        "/search?keyword={query}",
        "/watch/{slug}",
        "/ajax/episode/list/{id}",
        "/ajax/server/list?servers={id}",
        "/ajax/server?get={id}",
    ]
    _set_legos(
        anikoto,
        ANIKOTOTV,
        {
            "mirrors": [
                "https://anikototv.to",
                "https://anikoto.cz",
                "https://anikoto.me",
                "https://anikoto.net",
                "https://anikototv.se",
            ]
        },
    )

    after = json.dumps(value, ensure_ascii=False, sort_keys=True)
    changed = after != before
    if changed:
        OVERRIDES.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def validate() -> None:
    value = _load()
    patches = value["provider_patches"]
    expected = {
        "desiflix": (DESIFLIX, {"movie", "tv"}),
        "anikototv": (ANIKOTOTV, {"anime"}),
    }
    if isinstance(patches.get("allmovieland"), dict):
        expected["allmovieland"] = (ALLMOVIELAND, {"movie", "tv"})

    for provider_id, (script, required_types) in expected.items():
        row = _required_row(patches, provider_id)
        scripts = set(str(v) for v in row.get("provider_lego_scripts") or [])
        if script not in scripts:
            raise AssertionError(f"{provider_id}: missing clean-v3 route Lego {script}")
        published = set(str(v).lower() for v in row.get("published_types") or [])
        if published != required_types:
            raise AssertionError(
                f"{provider_id}: published type contract mismatch: {sorted(published)}"
            )
        routes = [str(v) for v in row.get("learned_routes") or []]
        if not routes:
            raise AssertionError(f"{provider_id}: missing stable learned_routes")

    desi_opts = patches["desiflix"].get("provider_lego_options", {}).get(DESIFLIX, {})
    if desi_opts.get("base") != "https://desiflix.stremioaddon.workers.dev":
        raise AssertionError("desiflix: responsive Worker must be primary runtime base")
    if desi_opts.get("fallbackBases") != ["https://manifest.desitvhub.eu.org"]:
        raise AssertionError("desiflix: official manifest fallback order mismatch")

    if isinstance(patches.get("allmovieland"), dict):
        all_routes = patches["allmovieland"]["learned_routes"]
        if any("session" in str(v).lower() or "aws" in str(v).lower() for v in all_routes):
            raise AssertionError("allmovieland: dynamic traversal URL leaked into stable DATA")

    anikoto = patches["anikototv"]
    if set(str(v).casefold() for v in anikoto.get("published_types") or []) != {"anime"}:
        raise AssertionError("anikototv: canonical movie widening is forbidden")
    ani_routes = [str(v).lower() for v in anikoto["learned_routes"]]
    if any("/v4/" in v or v.startswith("/api/") for v in ani_routes):
        raise AssertionError("anikototv: wrapper/obsolete route survived native-site migration")
    for required in ("/ajax/episode/list/{id}", "/ajax/server/list?servers={id}", "/ajax/server?get={id}"):
        if required not in ani_routes:
            raise AssertionError(f"anikototv: native AJAX route missing: {required}")


def main() -> int:
    changed = patch()
    validate()
    value = _load()
    has_allmovieland = isinstance((value.get("provider_patches") or {}).get("allmovieland"), dict)
    print(
        "PROVIDER_V3_BATCH_ROUTES_V1_OK "
        f"changed={str(changed).lower()} current=desiflix,anikototv "
        f"historical_allmovieland_present={str(has_allmovieland).lower()} anikototv_semantic=anime-only"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
