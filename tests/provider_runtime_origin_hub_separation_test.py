#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from materialize_provider_v3_all import provider_model  # noqa: E402
from provider_base_store import build_provider_data_model  # noqa: E402
from resolve_provider_hubs import _default_source_type  # noqa: E402
from validate_provider_v3_routes_sequential import provider_origins  # noqa: E402

MARKER = "NIAKVIO_PROVIDER_RUNTIME_ORIGIN_HUB_SEPARATION_V21"
VALIDATOR_MARKER = "NIAKVIO_PROVIDER_LIVE_GATE_HUB_ORIGIN_SEPARATION_V21"
TELEGRAM_DATA_MARKER = "NIAKVIO_PROVIDER_TELEGRAM_DISCOVERY_ONLY_DATA_V21_2"
TELEGRAM_RUNTIME_MARKER = "NIAKVIO_PROVIDER_TELEGRAM_DISCOVERY_ONLY_RUNTIME_V21_2"


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


def _contains_telegram(value: object) -> bool:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True).casefold()
    return any(token in text for token in ("https://t.me", "https://telegram.me", "https://telegram.dog"))


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


def test_live_gate_uses_same_origin_contract() -> None:
    model = {
        "knownSite": "https://all-wish.me",
        "officialSite": "https://all-wish.me",
        "officialHub": "https://t.me/s/allwishme",
        "officialApi": None,
        "fixedApi": None,
        "origins": ["https://all-wish.me"],
    }
    patch = {
        "official_site": "https://all-wish.me",
        "official_hub": "https://t.me/s/allwishme",
    }
    assert provider_origins(model, patch) == ["https://all-wish.me"], provider_origins(model, patch)


def test_telegram_hub_survives_for_domain_refresh_but_is_removed_from_executable_data() -> None:
    incoming = {
        "knownSite": "https://all-wish.me",
        "officialSite": "https://all-wish.me",
        "officialHub": "https://t.me/s/allwishme",
        "officialApi": None,
        "fixedApi": None,
        "strategy": "html_scraper",
        "routeProofVersion": 5,
        "identityInput": {"mode": "tmdb_direct", "requiresTmdbBeforeRun": False},
        "origins": ["https://all-wish.me", "https://t.me"],
        "observedUrls": ["https://all-wish.me/player", "https://t.me/s/allwishme"],
        "routes": ["/player", "/stream/getSources?id={id}"],
        # Simulate stale/bad historical proofs. These must never re-promote
        # Telegram into ProviderBase execution state.
        "proofSearchBases": ["https://t.me", "https://all-wish.me"],
        "proofDetailBases": ["https://telegram.me/allwishme", "https://all-wish.me"],
        "searchRequestPlan": [
            {
                "base": "https://t.me",
                "route": "/search?q={query}",
                "requestSpec": {"method": "GET"},
                "proofModelVersion": 5,
                "semanticTypes": ["movie"],
            },
            {
                "base": "https://all-wish.me",
                "route": "/search?q={query}",
                "requestSpec": {"method": "GET"},
                "proofModelVersion": 5,
                "semanticTypes": ["movie"],
            },
        ],
        "providerValuePlan": [
            {
                "searchBase": "https://telegram.dog/allwishme",
                "searchRoute": "/search?q={query}",
                "searchRequestSpec": {"method": "GET"},
                "steps": [{"base": "https://all-wish.me", "route": "/watch/{id}", "role": "detail"}],
                "proofModelVersion": 5,
                "semanticTypes": ["movie"],
            }
        ],
        "externalIdentityPlan": [
            {
                "base": "https://t.me",
                "route": "/detail/{imdbid}",
                "requestSpec": {"method": "GET"},
                "proofModelVersion": 5,
            }
        ],
    }
    data = build_provider_data_model(
        "synthetic",
        {"id": "synthetic", "name": "Synthetic", "supportedTypes": ["movie", "tv"]},
        known_site="https://all-wish.me",
        provider_model=incoming,
    )
    # Hub metadata is intentionally retained: Domain Refresh owns it.
    assert data["officialHub"] == "https://t.me/s/allwishme", data["officialHub"]
    assert _default_source_type(data["officialHub"], "latest_telegram_domain") == "telegram_public"

    # Every executable DATA field must be Telegram-free, even if old proof data
    # tried to promote Telegram into search/detail/API plans.
    for key in (
        "origins", "observedUrls", "proofSearchBases", "proofDetailBases",
        "searchRequestPlan", "providerValuePlan", "externalIdentityPlan",
    ):
        assert not _contains_telegram(data.get(key)), (key, data.get(key))
    assert "https://all-wish.me" in data["origins"], data["origins"]
    assert "https://all-wish.me" in data["proofSearchBases"], data["proofSearchBases"]


def test_current_allwish_data_does_not_execute_telegram() -> None:
    overrides = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
    knowledge = json.loads((ROOT / "automation/provider-v3-static-knowledge.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    patch = (overrides.get("provider_patches") or {}).get("allwish") or {}
    capability = (overrides.get("provider_capabilities") or {}).get("allwish") or {}
    static = (knowledge.get("providers") or {}).get("allwish") or {}
    entry = next(row for row in manifest.get("scrapers") or [] if str(row.get("id") or "").casefold() == "allwish")
    row = provider_model("allwish", patch, capability, static)
    assert row.get("officialHub"), row
    assert "https://t.me" not in (row.get("origins") or []), row.get("origins")
    assert any(str(v).startswith("https://all-wish.me") for v in (row.get("origins") or [])), row.get("origins")
    assert "https://t.me" not in provider_origins(row, patch), provider_origins(row, patch)

    data = build_provider_data_model(
        "allwish",
        entry,
        known_site=row.get("knownSite"),
        provider_model=row,
    )
    assert data.get("officialHub") == row.get("officialHub")
    for key in (
        "origins", "observedUrls", "proofSearchBases", "proofDetailBases",
        "searchRequestPlan", "providerValuePlan", "externalIdentityPlan",
    ):
        assert not _contains_telegram(data.get(key)), (key, data.get(key))


def main() -> int:
    materializer = (ROOT / "scripts/materialize_provider_v3_all.py").read_text(encoding="utf-8")
    validator = (ROOT / "scripts/validate_provider_v3_routes_sequential.py").read_text(encoding="utf-8")
    base_store = (ROOT / "scripts/provider_base_store.py").read_text(encoding="utf-8")
    assert MARKER in materializer, "runtime hub/origin separation marker missing"
    assert VALIDATOR_MARKER in validator, "live gate hub/origin separation marker missing"
    assert TELEGRAM_DATA_MARKER in base_store, "Telegram executable DATA filter missing"
    assert TELEGRAM_RUNTIME_MARKER in base_store, "Telegram runtime fetch guard missing"
    test_external_hub_is_not_runtime_origin()
    test_same_origin_site_hub_is_preserved()
    test_api_authority_survives_even_if_hub_matches()
    test_live_gate_uses_same_origin_contract()
    test_telegram_hub_survives_for_domain_refresh_but_is_removed_from_executable_data()
    test_current_allwish_data_does_not_execute_telegram()
    print(
        "PROVIDER_RUNTIME_ORIGIN_HUB_SEPARATION_OK "
        "external_hub_runtime=0 same_origin_site=1 api_authority=1 "
        "live_gate_hub_runtime=0 allwish_telegram_runtime=0 "
        "telegram_discovery_only=1 domain_refresh_telegram=1 stale_proof_telegram=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
