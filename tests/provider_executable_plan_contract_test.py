#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str((ROOT / "scripts").resolve()))

from provider_base_store import provider_model_has_executable_plan, provider_model_route_kind

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
    ("/api?m=stream&id={id}", "api"),
    ("/embed/{id}", "player"),
    ("/watch/{id}", "detail"),
    ("/track/pixel", "ignore"),
    ("/", "ignore"),
):
    assert provider_model_route_kind(route) == expected, (route, provider_model_route_kind(route), expected)

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
assert '"providerExecutablePlan": "passed"' in activation

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
