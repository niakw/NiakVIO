#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
OVERRIDES = ROOT / "provider-overrides.json"
KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"
EXPECTED = 96


def canonical(value: object) -> str:
    return "".join(ch for ch in str(value or "").strip().casefold() if ch.isalnum() or ch in "-_")


manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
overrides = json.loads(OVERRIDES.read_text(encoding="utf-8"))
knowledge = json.loads(KNOWLEDGE.read_text(encoding="utf-8"))

assert knowledge.get("schemaVersion") == 1
assert knowledge.get("providerCount") == EXPECTED
assert knowledge.get("legacyProviderJsExecuted") is False
assert knowledge.get("upstreamJsExecuted") is False
assert knowledge.get("role") == "durable-structured-provider-data"

manifest_ids = {
    canonical(row.get("id"))
    for row in manifest.get("scrapers") or []
    if isinstance(row, dict)
}
providers = knowledge.get("providers")
assert isinstance(providers, dict)
assert manifest_ids == set(providers), (sorted(manifest_ids - set(providers)), sorted(set(providers) - manifest_ids))

patches = overrides.get("provider_patches") or {}
unusable = []
routeful = 0
for provider_id in sorted(manifest_ids):
    row = providers[provider_id]
    assert row.get("legacyProviderJsExecuted") is False
    assert row.get("upstreamJsExecuted") is False
    model = row.get("model")
    assert isinstance(model, dict)
    sources = row.get("sources")
    assert isinstance(sources, list) and sources, provider_id
    assert all(source.get("codeRole") == "knowledge-only" and source.get("codeExecuted") is False for source in sources)

    if model.get("routes"):
        routeful += 1
    patch = patches.get(provider_id) if isinstance(patches.get(provider_id), dict) else {}
    has_plan = bool(
        model.get("knownSite")
        or model.get("officialSite")
        or model.get("officialApi")
        or model.get("fixedApi")
        or model.get("routes")
        or model.get("observedUrls")
        or model.get("origins")
        or isinstance(model.get("apiRecipe"), dict)
        or (isinstance(patch.get("api_recipe"), dict))
        or (isinstance(patch.get("provider_lego_scripts"), list) and patch.get("provider_lego_scripts"))
    )
    if not has_plan:
        unusable.append(provider_id)

assert not unusable, unusable
assert routeful >= 30, routeful

for provider_id in ("purstream", "vegamovies", "hindmoviez", "animezey", "4khdhubnew", "vidlove", "castle", "kehflix", "streamzo"):
    assert provider_id in providers
    model = providers[provider_id]["model"]
    assert any(
        [
            model.get("routes"),
            model.get("observedUrls"),
            model.get("origins"),
            model.get("knownSite"),
            model.get("officialApi"),
            isinstance(model.get("apiRecipe"), dict),
            (patches.get(provider_id) or {}).get("provider_lego_scripts"),
        ]
    ), provider_id

print(f"Provider v3 durable static knowledge contract passed providers={len(providers)} routeful={routeful}")
