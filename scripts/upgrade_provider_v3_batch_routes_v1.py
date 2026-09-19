#!/usr/bin/env python3
"""Idempotently wire current clean-v3 route Lego for the #9-#18 provider batch.

Historical providers may remain in knowledge/provenance, but this migration only
mutates providers present in the current manifest. Transport aliases never create
canonical semantic lanes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
MANIFEST = ROOT / "manifest.json"

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


def _current_provider_ids() -> set[str]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {
        str(row.get("id") or "").strip().casefold()
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }


def _row(patches: dict[str, Any], provider_id: str) -> dict[str, Any]:
    row = patches.get(provider_id)
    if not isinstance(row, dict):
        raise AssertionError(f"missing provider patch row: {provider_id}")
    return row


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
    current = _current_provider_ids()
    before = json.dumps(value, ensure_ascii=False, sort_keys=True)

    if "desiflix" in current:
        desiflix = _row(patches, "desiflix")
        desiflix["published_types"] = ["movie", "tv"]
        desiflix["learned_routes"] = [
            "/stream/movie/{id}.json",
            "/stream/series/{id}:{season}:{episode}.json",
        ]
        _set_legos(
            desiflix,
            DESIFLIX,
            {
                "base": "https://desiflix.stremioaddon.workers.dev",
                "fallbackBases": ["https://manifest.desitvhub.eu.org"],
            },
        )

    if "allmovieland" in current:
        allmovieland = _row(patches, "allmovieland")
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

    if "anikototv" in current:
        anikoto = _row(patches, "anikototv")
        anikoto["published_types"] = ["anime"]
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

    changed = json.dumps(value, ensure_ascii=False, sort_keys=True) != before
    if changed:
        OVERRIDES.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def validate() -> None:
    value = _load()
    patches = value["provider_patches"]
    current = _current_provider_ids()
    expected = {
        "desiflix": (DESIFLIX, {"movie", "tv"}),
        "allmovieland": (ALLMOVIELAND, {"movie", "tv"}),
        "anikototv": (ANIKOTOTV, {"anime"}),
    }

    for provider_id, (script, required_types) in expected.items():
        if provider_id not in current:
            continue
        row = _row(patches, provider_id)
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

    if "desiflix" in current:
        desi_opts = patches["desiflix"].get("provider_lego_options", {}).get(DESIFLIX, {})
        if desi_opts.get("base") != "https://desiflix.stremioaddon.workers.dev":
            raise AssertionError("desiflix: responsive Worker must be primary runtime base")
        if desi_opts.get("fallbackBases") != ["https://manifest.desitvhub.eu.org"]:
            raise AssertionError("desiflix: official manifest fallback order mismatch")

    if "allmovieland" in current:
        all_routes = patches["allmovieland"]["learned_routes"]
        if any("session" in str(v).lower() or "aws" in str(v).lower() for v in all_routes):
            raise AssertionError("allmovieland: dynamic traversal URL leaked into stable DATA")

    if "anikototv" in current:
        ani_routes = [str(v).lower() for v in patches["anikototv"]["learned_routes"]]
        if any("/v4/" in v or v.startswith("/api/") for v in ani_routes):
            raise AssertionError("anikototv: wrapper/obsolete route survived native-site migration")
        for required in (
            "/ajax/episode/list/{id}",
            "/ajax/server/list?servers={id}",
            "/ajax/server?get={id}",
        ):
            if required not in ani_routes:
                raise AssertionError(f"anikototv: native AJAX route missing: {required}")


def main() -> int:
    changed = patch()
    validate()
    providers = sorted(_current_provider_ids() & {"desiflix", "allmovieland", "anikototv"})
    print(
        "PROVIDER_V3_BATCH_ROUTES_V1_OK "
        f"changed={str(changed).lower()} providers={','.join(providers)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
