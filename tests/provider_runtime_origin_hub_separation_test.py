#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from materialize_provider_v3_all import provider_model  # noqa: E402

MARKER = "NIAKVIO_PROVIDER_RUNTIME_ORIGIN_HUB_SEPARATION_V21"


def model_for(*, site: str, hub: str, api: str | None = None, static_origins: list[str] | None = None) -> dict:
    patch = {
        "official_site": site,
        "official_hub": hub,
        "official_api": api,
        "route_proof_version": 5,
        "learned_routes": [],
        "capability": "html_scraper",
    }
    capability = {"strategy": "html_scraper", "types": ["movie", "tv"]}
    static = {
        "model": {
            "officialSite": site,
            "officialHub": hub,
            "officialApi": api,
            "origins": list(static_origins or []),
            "supportedTypes": ["movie", "tv"],
            "routeProofVersion": 5,
        }
    }
    return provider_model("synthetic", patch, capability, static)


def test_external_hub_is_not_runtime_origin() -> None:
    row = model_for(
        site="https://all-wish.me",
        hub="https://t.me/s/allwishme",
        static_origins=["https://all-wish.me", "https://t.me"],
    )
    assert row["officialHub"] == "https://t.me/s/allwishme"
    assert row["origins"] == ["https://all-wish.me"], row["origins"]


def test_same_origin_site_hub_is_preserved() -> None:
    row = model_for(
        site="https://anime-sama.wiki/",
        hub="https://anime-sama.wiki/adresse",
        static_origins=["https://anime-sama.wiki"],
    )
    assert row["origins"] == ["https://anime-sama.wiki"], row["origins"]


def test_api_authority_survives_even_if_hub_matches() -> None:
    row = model_for(
        site="https://provider.test",
        hub="https://api.provider.test/status",
        api="https://api.provider.test/v1",
        static_origins=["https://api.provider.test"],
    )
    assert row["origins"] == ["https://provider.test", "https://api.provider.test"], row["origins"]


def test_current_allwish_data_does_not_execute_telegram() -> None:
    overrides = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
    knowledge = json.loads((ROOT / "automation/provider-v3-static-knowledge.json").read_text(encoding="utf-8"))
    patch = (overrides.get("provider_patches") or {}).get("allwish") or {}
    capability = (overrides.get("provider_capabilities") or {}).get("allwish") or {}
    static = (knowledge.get("providers") or {}).get("allwish") or {}
    row = provider_model("allwish", patch, capability, static)
    assert row.get("officialHub"), row
    assert "https://t.me" not in (row.get("origins") or []), row.get("origins")
    assert any(str(v).startswith("https://all-wish.me") for v in (row.get("origins") or [])), row.get("origins")


def main() -> int:
    source = (ROOT / "scripts/materialize_provider_v3_all.py").read_text(encoding="utf-8")
    assert MARKER in source, "runtime hub/origin separation marker missing"
    test_external_hub_is_not_runtime_origin()
    test_same_origin_site_hub_is_preserved()
    test_api_authority_survives_even_if_hub_matches()
    test_current_allwish_data_does_not_execute_telegram()
    print("PROVIDER_RUNTIME_ORIGIN_HUB_SEPARATION_OK external_hub_runtime=0 same_origin_site=1 api_authority=1 allwish_telegram_runtime=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
