#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str((ROOT / "scripts").resolve()))

from provider_base_store import provider_model_has_executable_plan, provider_model_has_identity_execution_plan, provider_model_route_kind, provider_route_has_fixed_content_identity, provider_route_is_identity_aware

direct_only = {
    "providerId": "direct-only",
    "strategy": "mixed_embed_resolver",
    "knownSite": "https://example.invalid",
    "officialSite": "https://example.invalid",
    "routes": [],
    "apiRecipe": None,
    "providerValuePlan": [],
    "searchRequestPlan": [],
    "externalIdentityPlan": [],
}
assert provider_model_has_executable_plan(direct_only) is False

for route, expected in (
    ("/search?q={query}", "search"),
    ("/index.php?do=search&subaction=search&story={query}", "search"),
    ("/api?m=stream&id={id}", "api"),
    ("/embed/{id}", "player"),
    ("/watch/{id}", "detail"),
    ("/track/pixel", "ignore"),
    ("/", "ignore"),
):
    assert provider_model_route_kind(route) == expected, (route, provider_model_route_kind(route), expected)


assert provider_model_has_executable_plan({**direct_only, "routes": ["/api/push/subscribe"]}) is True
assert provider_model_has_identity_execution_plan({**direct_only, "routes": ["/api/push/subscribe"]}) is False
assert provider_model_has_identity_execution_plan({**direct_only, "routes": ["/embed/sw.js"]}) is False
assert provider_model_has_identity_execution_plan({**direct_only, "routes": ["/series"]}) is False
assert provider_model_has_identity_execution_plan({**direct_only, "routes": ["/search"]}) is False
assert provider_model_has_identity_execution_plan({**direct_only, "routes": ["/movie/{tmdbId}"]}) is True
assert provider_route_has_fixed_content_identity("/movie/157336-interstellar") is True
assert provider_route_has_fixed_content_identity("/tv/1399-breaking-bad?s={query}") is True
assert provider_route_has_fixed_content_identity("/embed/157336?parent_origin=x") is True
assert provider_route_has_fixed_content_identity("/movie/{tmdbId}-{slug}") is False
assert provider_route_has_fixed_content_identity("/watch/{binding:contentId}") is False
assert provider_route_has_fixed_content_identity("/api/source/12345") is False
assert provider_route_is_identity_aware("/movie/157336-{slug}") is False
assert provider_route_is_identity_aware("/tv/1399-breaking-bad?q={query}") is False
assert provider_route_is_identity_aware("/api/session-handoff/issue") is False
assert provider_route_is_identity_aware("/search?q={query}") is True
assert provider_route_is_identity_aware("/index.php?do=search&subaction=search&story={query}") is True
assert provider_model_has_executable_plan({**direct_only, "routes": ["/index.php?do=search&subaction=search&story={query}"]}) is True
assert provider_model_has_identity_execution_plan({**direct_only, "routes": ["/index.php?do=search&subaction=search&story={query}"]}) is True

for model in (
    {**direct_only, "routes": ["/search?q={query}"]},
    {**direct_only, "routes": ["/watch/{id}"]},
    {**direct_only, "apiRecipe": {}},
    {**direct_only, "providerValuePlan": [{"searchBase": "https://example.invalid"}]},
    {**direct_only, "searchRequestPlan": [{"base": "https://example.invalid"}]},
    {**direct_only, "externalIdentityPlan": [{"base": "https://example.invalid"}]},
):
    assert provider_model_has_executable_plan(model) is True, model

activation = (ROOT / "scripts" / "activate_bulk_offline_proven_providers.py").read_text(encoding="utf-8")
assert "provider_model_has_executable_plan" in activation
assert "provider_v3_executable_plan_missing" in activation
assert "provider_v3_identity_execution_plan_missing" in activation
assert '"providerExecutablePlan": "passed"' in activation
assert '"providerIdentityExecutionPlan": "passed"' in activation

materializer = (ROOT / "scripts" / "materialize_provider_v3_all.py").read_text(encoding="utf-8")
assert "provider_route_has_fixed_content_identity" in materializer
assert "not provider_route_has_fixed_content_identity(value)" in materializer
assert "not provider_route_has_fixed_content_identity(item)" in materializer

import materialize_provider_v3_all as materializer_module

owned_external_patch = {
    "capability": "api_stream_resolver",
    "official_site": "https://www.example.invalid",
    "official_api": "https://api.example.invalid",
    "learned_routes": [
        "/seed?mediaId={tmdbId}",
        "/miami/sources",
    ],
    "provider_lego_scripts": ["scripts/provider_patches/example_external_id_runtime_v1.py"],
    "identity_input": {
        "mode": "external_id",
        "requires_tmdb_before_run": True,
        "required_fields": ["tmdbId", "mediaType", "imdbId"],
    },
}
assert materializer_module.provider_patch_has_owned_identity_lego_execution(owned_external_patch)

owned_catalogue_patch = {
    "provider_lego_scripts": ["scripts/provider_patches/example_catalogue_runtime_v1.py"],
    "identity_input": {
        "mode": "catalog_search",
        "requires_tmdb_before_run": True,
        "required_fields": ["title", "mediaType"],
    },
}
assert materializer_module.provider_patch_has_owned_identity_lego_execution(owned_catalogue_patch)
assert not materializer_module.provider_patch_has_owned_identity_lego_execution({
    **owned_catalogue_patch,
    "identity_input": {
        "mode": "catalog_search",
        "requires_tmdb_before_run": True,
        "required_fields": ["tmdbId", "mediaType"],
    },
})
assert not materializer_module.provider_patch_has_owned_identity_lego_execution({
    **owned_catalogue_patch,
    "identity_input": {
        "mode": "catalog_search",
        "requires_tmdb_before_run": False,
        "required_fields": ["title", "mediaType"],
    },
})

owned_external_model = materializer_module.provider_model(
    "example-owned-lego",
    owned_external_patch,
    {"strategy": "api_stream_resolver", "validation": "physical_mac_terminal_oracle"},
    {"model": {}},
)
assert "/seed?mediaId={tmdbId}" in owned_external_model["routes"], owned_external_model
assert provider_model_has_executable_plan(owned_external_model)
assert provider_model_has_identity_execution_plan(owned_external_model)
assert owned_external_model["routeProofVersion"] == 0

base = (ROOT / "scripts" / "provider_base_store.py").read_text(encoding="utf-8")
runtime = base.split("function _runtimePlanAvailable() {", 1)[1].split("\n}", 1)[0]
for token in (
    "NIAKVIO_PROVIDER_MODEL.apiRecipe",
    "NIAKVIO_PROVIDER_MODEL.providerValuePlan",
    "NIAKVIO_PROVIDER_MODEL.searchRequestPlan",
    "NIAKVIO_PROVIDER_MODEL.externalIdentityPlan",
    '["search","detail","player","api"]',
):
    assert token in runtime, f"Python executable-plan mirror drifted from runtime: {token}"

print("Provider executable-plan activation contract passed")
