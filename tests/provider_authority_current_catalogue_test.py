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
pending = module.pending_provider_ids()

def classify(provider: str) -> dict:
    return module.classify(
        provider,
        rows[provider],
        registries.get(provider) if isinstance(registries.get(provider), dict) else {},
        patches.get(provider) if isinstance(patches.get(provider), dict) else {},
        histories.get(provider) if isinstance(histories.get(provider), dict) else {},
        pending_onboarding=provider in pending,
    )

# Manual withdrawals are authoritative only when their decision is explicitly
# persisted. This is a lifecycle *class*, not a provider-specific fixture:
# subsequent cohorts must not require modifying this test to permit disable.
def expected_with_lifecycle(provider: str, baseline: str) -> str:
    if provider not in rows:
        return baseline
    if provider in pending:
        return "ONBOARDING_PENDING"
    if rows[provider].get("enabled") is False:
        return "KEEP_DISABLED"
    registry = registries.get(provider) or {}
    patch = patches.get(provider) or {}
    reason = str(registry.get("manual_off_reason") or patch.get("manual_off_reason") or "").strip()
    if not reason:
        return baseline
    if reason.startswith("manual_off_zero_playable_"):
        selection = registry.get("lifecycle_selection") or {}
        assert selection.get("status") == "provisional-disabled-pending-native-proof", (provider, selection)
        assert str(selection.get("date") or "").strip(), (provider, selection)
        assert str(selection.get("reason") or "").strip(), (provider, selection)
        assert str(selection.get("censusRun") or "").strip(), (provider, selection)
        assert int(selection.get("retentionDays") or 0) == 7, (provider, selection)
    return "KEEP_DISABLED" if rows[provider].get("enabled") is False else "DISABLE_MANUAL_POLICY"

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
    "showbox": (
        "DISABLE_MANUAL_POLICY"
        if "showbox" in rows and rows["showbox"].get("enabled") is not False
        else "KEEP_DISABLED"
    ),
    "animetsu": "KEEP_DISABLED",
    "fullanime": "KEEP_DISABLED",
    "desiflix": "KEEP_DISABLED",
}
archived = lifecycle.get("archived") if isinstance(lifecycle.get("archived"), dict) else {}

# Every evidence-backed zero-playback withdrawal must traverse the same
# disable -> retention -> archive transition, regardless of provider/genre.
for provider, registry in registries.items():
    if not isinstance(registry, dict):
        continue
    reason = str(registry.get("manual_off_reason") or "")
    if not reason.startswith("manual_off_zero_playable_"):
        continue
    if provider in rows:
        result = classify(provider)
        expected_action = expected_with_lifecycle(provider, "KEEP_DIAGNOSTIC")
        assert result["action"] == expected_action, (provider, expected_action, result)
        assert result["repairEligible"] is False, (provider, result)
    else:
        record = archived.get(provider) or {}
        assert record.get("state") == "archived-provider-old", (provider, record)
        assert record.get("reason") == reason, (provider, record)

for provider, baseline_action in expected.items():
    action = expected_with_lifecycle(provider, baseline_action)
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

# Disabled production rows are terminal lifecycle authority. Once a row has
# entered retention it must not remain a Repair candidate merely because older
# direct/route authority still exists.
for provider, row in rows.items():
    if row.get("enabled") is not False or provider in pending:
        continue
    result = classify(provider)
    assert result["action"] == "KEEP_DISABLED", (provider, result)
    assert result["repairEligible"] is False, (provider, result)
for provider in sorted(pending):
    assert provider in rows and rows[provider].get("enabled") is False, provider
    result=classify(provider)
    assert result["action"] == "ONBOARDING_PENDING", (provider,result)
    assert result["repairEligible"] is False, (provider,result)

# Any current-tested production identity lacking terminal playback may be moved
# into disabled retention before this catalogue contract runs. This is
# status-driven, never a provider-specific exception list.
census = json.loads((ROOT / "automation/provider-census-status.json").read_text(encoding="utf-8"))
withdrawn_current = set()
for proof in census.get("providers") or []:
    if not isinstance(proof, dict):
        continue
    provider = str(proof.get("provider") or "").strip().casefold().replace("_", "-")
    if (
        module.current_architecture_nonfunctional(proof)
        and provider in rows
        and rows[provider].get("enabled") is False
    ):
        withdrawn_current.add(provider)
        result = classify(provider)
        assert result["action"] == "KEEP_DISABLED", (provider, result)
        assert result["repairEligible"] is False, (provider, result)

# Explicit-current authority remains useful for Repair while active, but current
# runtime evidence wins the production activation decision. Do not special-case
# an identity merely because its address authority is strong.
animesultra = classify("animesultra")
if rows["animesultra"].get("enabled") is False or "animesultra" in withdrawn_current:
    assert animesultra["action"] == "KEEP_DISABLED", animesultra
    assert animesultra["repairEligible"] is False, animesultra
else:
    assert animesultra["action"] == "KEEP_DIRECT", animesultra
    assert animesultra["failureCount"] == 0, animesultra

# Search is still available for the historical catalogue, but never as current
# authority by itself. ShowBox has now been explicitly marked non-activable after
# manual source review found no public authority beyond search/private Telegram.
# Before lifecycle apply it must request DISABLE_MANUAL_POLICY; after apply it is
# terminal KEEP_DISABLED. New registry autofill rows still opt out by default.
if "showbox" in rows:
    showbox_registry = registries["showbox"]
    showbox = classify("showbox")
    assert showbox["reasons"] == ["manual_off_no_current_authority_search_only"], showbox
    assert showbox_registry.get("legacy_search_refresh") is True, showbox_registry
    assert showbox_registry.get("activation_eligible") is False, showbox_registry
    assert showbox_registry.get("direct") is None, showbox_registry
    assert showbox["confidence"] == "terminal", showbox
else:
    showbox_record = archived.get("showbox")
    assert isinstance(showbox_record, dict), showbox_record
    assert showbox_record.get("state") == "archived-provider-old", showbox_record
for provider, row in registries.items():
    if isinstance(row, dict) and row.get("registry_state") == "unresolved":
        assert row.get("legacy_search_refresh") is not True, (provider, row)
        assert not row.get("direct") and not row.get("hub"), (provider, row)

print("provider current catalogue authority contract ok")
