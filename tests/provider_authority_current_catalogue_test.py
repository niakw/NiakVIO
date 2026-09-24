#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "classify_provider_authority.py"
spec = importlib.util.spec_from_file_location("provider_authority", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
hubs = json.loads((ROOT / "provider-hubs.json").read_text(encoding="utf-8"))
overrides = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
history = json.loads((ROOT / "provider-domain-history.json").read_text(encoding="utf-8"))
lifecycle = json.loads((ROOT / "automation/provider-disabled-lifecycle.json").read_text(encoding="utf-8"))

rows = {
    str(row.get("id") or "").strip().casefold(): row
    for row in manifest.get("scrapers") or []
    if isinstance(row, dict)
}
registries = hubs.get("providers") or {}
patches = overrides.get("provider_patches") or {}
histories = history.get("providers") or {}

def classify(provider: str) -> dict:
    return module.classify(
        provider,
        rows[provider],
        registries.get(provider) if isinstance(registries.get(provider), dict) else {},
        patches.get(provider) if isinstance(patches.get(provider), dict) else {},
        histories.get(provider) if isinstance(histories.get(provider), dict) else {},
    )

expected = {
    "yflix": "KEEP_BACKEND",
    "persianstremio": "KEEP_BACKEND",
    "vidfast": "KEEP_ROUTE_AUTHORITY",
    "kurage": "KEEP_DIRECT",
    "sekai": "KEEP_DIRECT",
    "streamzo": "KEEP_DIRECT",
    "voiranime-rip": "KEEP_DIRECT",
    "animekai": "KEEP_PROVEN_SITE",
    "neko-sama": "KEEP_PROVEN_SITE",
    "anime-ultime": "KEEP_PROVEN_SITE",
    "mallumv": "KEEP_PROVEN_SITE",
    "showbox": "DISABLE_MANUAL_POLICY" if rows["showbox"].get("enabled") is not False else "KEEP_DISABLED",
    "animetsu": "KEEP_DISABLED",
    "fullanime": "KEEP_DISABLED",
    "desiflix": "KEEP_DISABLED",
}
archived = lifecycle.get("archived") if isinstance(lifecycle.get("archived"), dict) else {}
for provider, action in expected.items():
    if provider not in rows:
        record = archived.get(provider) if isinstance(archived.get(provider), dict) else None
        assert record is not None, (provider, "missing-from-current-manifest-without-archive-state")
        assert record.get("state") == "archived-provider-old", (provider, record)
        assert action == "KEEP_DISABLED", (provider, action, record)
        continue
    result = classify(provider)
    assert result["action"] == action, (provider, result)
    if action.startswith("KEEP_") and action != "KEEP_DISABLED":
        assert result["repairEligible"] is True, (provider, result)
    if action in {"KEEP_DISABLED", "REDISCOVER_SEARCH", "DISABLE_MANUAL_POLICY"}:
        assert result["repairEligible"] is False, (provider, result)

# An explicit-current site is allowed while Domain has no persisted contradiction.
# Domain failure memory, not a human hunch or raw search result, must demote it.
animesultra = classify("animesultra")
assert animesultra["action"] == "KEEP_DIRECT", animesultra
assert animesultra["failureCount"] == 0, animesultra

# Search is still available for the historical catalogue, but never as current
# authority by itself. ShowBox has now been explicitly marked non-activable after
# manual source review found no public authority beyond search/private Telegram.
# Before lifecycle apply it must request DISABLE_MANUAL_POLICY; after apply it is
# terminal KEEP_DISABLED. New registry autofill rows still opt out by default.
showbox_registry = registries["showbox"]
showbox = classify("showbox")
assert showbox["reasons"] == ["manual_off_no_current_authority_search_only"], showbox
assert showbox_registry.get("legacy_search_refresh") is True, showbox_registry
assert showbox_registry.get("activation_eligible") is False, showbox_registry
assert showbox_registry.get("direct") is None, showbox_registry
assert showbox["confidence"] == "terminal", showbox
for provider, row in registries.items():
    if isinstance(row, dict) and row.get("registry_state") == "unresolved":
        assert row.get("legacy_search_refresh") is not True, (provider, row)
        assert not row.get("direct") and not row.get("hub"), (provider, row)

print("provider current catalogue authority contract ok")
