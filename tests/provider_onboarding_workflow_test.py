#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADD = (ROOT / ".github/workflows/add-provider.yml").read_text(encoding="utf-8")
BRANDING = (ROOT / ".github/workflows/provider-branding-assets.yml").read_text(encoding="utf-8")
CORE = (ROOT / ".github/workflows/core-media-finalize-main.yml").read_text(encoding="utf-8")
ONBOARD = (ROOT / "scripts/add_provider.py").read_text(encoding="utf-8")
ASSETS = (ROOT / "scripts/provider_branding_assets.py").read_text(encoding="utf-8")
LEARNING = (ROOT / "scripts/run_brain_learning_queue.py").read_text(encoding="utf-8")
IOS = (ROOT / ".github/workflows/native-mobile-ios-reader.yml").read_text(encoding="utf-8")
IOS_SUITE = (ROOT / "scripts/run_native_corpus_ios_suite.sh").read_text(encoding="utf-8")

# Full-auto provider onboarding accepts structured knowledge, never executable
# source, and shares the exact same production writer lane as Core/provider sync.
assert "workflow_dispatch:" in ADD
assert '".github/provider-onboarding/request.json"' in ADD
for field in ("hub:", "direct:", "telegram:", "api:", "search_queries:", "types:", "languages:", "formats:"):
    assert field in ADD, field
assert "group: nuvio-provider-publish-main" in ADD
assert "group: nuvio-provider-publish-main" in CORE
assert "cancel-in-progress: false" in ADD
assert "cancel-in-progress: false" in CORE
assert "scripts/add_provider.py stage" in ADD
assert "scripts/add_provider.py refresh" in ADD
assert "scripts/add_provider.py finalize" in ADD
assert "resolve_provider_hubs.py" in ADD
assert "resolve_provider_hub_search_fallback.py" in ADD
assert "provider_branding_assets.py" in ADD and "--mode only" in ADD
assert "nuvio_client_lab.cjs" in ADD
assert "npm test" in ADD

assert "persist_clean_provider_seed(" in ONBOARD
assert "CLEAN_RECONSTRUCTION_SOURCE" in ONBOARD
assert '"type": "hub"' in ONBOARD
assert '"type": "direct"' not in ONBOARD
assert '"type": "telegram_public"' in ONBOARD
assert '"type": "api"' not in ONBOARD
assert '"direct_candidates"' in ONBOARD
assert '"api_templates"' in ONBOARD
assert '"type": "search"' in ONBOARD
assert "upstream" not in ONBOARD.casefold() or "upstream_id" in ONBOARD
assert "clean_reconstruction_verified" in ONBOARD

# Incremental branding is the default onboarding path. The all-provider rebuild
# remains explicitly manual and is never scheduled or push-triggered.
assert "workflow_dispatch:" in BRANDING
assert "\n  schedule:" not in BRANDING
assert "\n  push:" not in BRANDING
assert "- only" in BRANDING and "- full" in BRANDING
assert "--mode only" in BRANDING and "--mode full" in BRANDING
assert 'choices=("only", "full")' in ASSETS
assert 'targets = [provider_id]' in ASSETS
assert 'targets = manifest_ids' in ASSETS

# Learning keeps one warm Lab process and strict quick parameters.
assert "class LearningLabSession" in LEARNING
assert "subprocess.Popen(" in LEARNING
assert '"provider_timeout_ms": 12000' in LEARNING
assert '"retry_provider_timeouts": False' in LEARNING
assert '"max_settings_profiles": 1' in LEARNING
assert '"max_streams_per_runtime": max(1, min(int(stream_cap), 2))' in LEARNING
assert '"playback_timeout_ms": 5000' in LEARNING

# iOS exposes the same quick/full distinction. Device IPA is a full gate;
# Learning reuses the installed simulator app instead of rebuilding per provider.
assert "mode:" in IOS and "- full" in IOS and "- learning" in IOS
assert "inputs.mode != 'learning'" in IOS
assert "./scripts/build-ios-ipa.sh" in IOS
assert "NIAKVIO_IOS_TARGET_PROVIDER" in IOS
assert "FIELD_NATIVE_IOS_SESSION state=warm-created" in IOS_SUITE
assert "FIELD_NATIVE_IOS_SESSION state=warm-reused" in IOS_SUITE
assert 'xcrun simctl launch --terminate-running-process' in IOS_SUITE

# Full native platform Labs remain weekly + manual, never push-triggered.
for path in (
    ".github/workflows/native-mobile-android-reader.yml",
    ".github/workflows/native-mobile-ios-reader.yml",
    ".github/workflows/native-desktop-reader-acceptance.yml",
):
    workflow = (ROOT / path).read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow, path
    assert "\n  schedule:" in workflow, path
    if "\n  push:" in workflow:
        assert ".github/triggers/full-native-lab-validation.json" in workflow, path

assert not (ROOT / ".github/workflows/native-tv-route-reader.yml").exists()
print("provider onboarding/Learning Lab architecture contract passed")
