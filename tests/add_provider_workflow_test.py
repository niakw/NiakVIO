#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/add-provider.yml").read_text(encoding="utf-8")
script = (ROOT / "scripts/add_provider.py").read_text(encoding="utf-8")
intake = json.loads((ROOT / "provider-intake/kehflix.json").read_text(encoding="utf-8"))
resolver = (ROOT / "scripts/resolve_provider_hubs.py").read_text(encoding="utf-8")

assert "workflow_dispatch:" in workflow
assert 'provider-intake/*.json' in workflow
assert "permissions:\n  contents: write" in workflow
assert "scripts/add_provider.py" in workflow
assert "resolve_provider_hubs.py" in workflow
assert "--provider" in workflow and "--mode deep" in workflow
assert "stage_published.py" in workflow
assert "health_check.mjs" in workflow
assert "npm test" in workflow
assert "native-tv-route-reader.yml" not in workflow
assert "native-mobile-android-reader.yml" not in workflow
assert "native-mobile-ios-reader.yml" not in workflow
assert "native-desktop-reader-acceptance.yml" not in workflow

for required in (
    "persist_clean_provider_seed",
    "CLEAN_RECONSTRUCTION_SOURCE",
    "thirdPartyProviderCodeExecuted",
    "activationRequiresCurrentTargetedProof",
    "weeklyFullNativeLabsRemainIndependent",
):
    assert required in script, required

assert intake["id"] == "kehflix"
assert intake["hub"] == "https://kehflix.wiki/"
assert intake["direct"] == "https://kehflix.com/"
assert intake["official_link_labels"] == ["Entrer"]
assert intake["supportedTypes"] == ["movie", "tv", "anime"]
assert '"Entrer"' in resolver

print("add-provider full-auto workflow contract passed")
