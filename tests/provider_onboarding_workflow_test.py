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
# source. Validation and publication use isolated latest-wins lanes; the writer
# rebases on current main rather than blocking unrelated Core publication work.
assert "workflow_dispatch:" in ADD
assert '".github/provider-onboarding/request.json"' in ADD
for field in ("hub:", "direct:", "telegram:", "api:", "search_queries:", "types:", "languages:", "formats:"):
    assert field in ADD, field
assert "group: niakvio-add-provider-publication-main" in ADD
assert "group: nuvio-provider-publish-main" in CORE
assert "cancel-in-progress: true" in ADD
assert "cancel-in-progress: true" in CORE
assert "group: nuvio-provider-onboarding-stage-main" in ADD
assert "cancel-in-progress: true" in ADD
assert "provider-onboarding-transaction-${{ github.run_id }}" in ADD
assert "actions/download-artifact@" in ADD
assert "git apply --3way --index" in ADD
assert "git fetch origin main" in ADD
assert "git rebase origin/main" in ADD
assert "needs: onboard" in ADD
assert ADD.index("group: nuvio-provider-onboarding-stage-main") < ADD.index("group: niakvio-add-provider-publication-main")
assert "scripts/add_provider.py stage" in ADD
assert "scripts/add_provider.py refresh" in ADD
assert "scripts/add_provider.py finalize" in ADD
assert "resolve_provider_hubs.py" in ADD
assert "resolve_provider_hub_search_fallback.py" in ADD
assert "probe_provider_site_structure.py" in ADD
assert "provider_branding_assets.py" in ADD and "--mode only" in ADD
assert ADD.count("nuvio_client_lab.cjs") >= 2
assert "final-lab-report.json" in ADD
assert "FIELD_PROVIDER_ONBOARDING_FINAL_LAB" in ADD
assert ADD.index("Rebuild exact publication after activation decision") < ADD.index("Verify exact rebuilt provider on first declared type")
assert ADD.index("Verify exact rebuilt provider on first declared type") < ADD.index("Rebuild publication after exact verification")
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

SITE_PROBE = (ROOT / "scripts/probe_provider_site_structure.py").read_text(encoding="utf-8")
assert 'f"/title/{kind}/{quote(tmdb_id)}-{quote(slug)}"' in SITE_PROBE
assert 'f"/title/{kind}/{quote(tmdb_id)}"' in SITE_PROBE
assert 'page_is_detail = "/title/" in urlsplit(final).path' in SITE_PROBE
assert 'priority = (100 if page_is_detail else 10)' in SITE_PROBE
assert "RUNTIME_API_LITERAL" in SITE_PROBE
assert "runtime_api_patterns" in SITE_PROBE
assert "runtime_api_probes" in SITE_PROBE
assert '"--max-runtime-chunks"' in SITE_PROBE
assert "default=18" in SITE_PROBE

SITE_WORKFLOW = (ROOT / ".github/workflows/provider-site-probe.yml").read_text(encoding="utf-8")
RUNTIME_PARITY = (ROOT / "scripts/probe_provider_runtime_parity.py").read_text(encoding="utf-8")
assert "probe_provider_runtime_parity.py" in SITE_WORKFLOW
assert "provider-runtime-parity.json" in SITE_WORKFLOW
assert "capture_output=True" in RUNTIME_PARITY
assert '"network_observations": observations[:80]' in RUNTIME_PARITY
assert '"onboarding_tv"' in RUNTIME_PARITY
assert '"onboarding_compose"' in RUNTIME_PARITY
assert "def committed_base_path" in RUNTIME_PARITY
assert '["git", "show", "HEAD:PROVENANCE.json"]' in RUNTIME_PARITY
assert '"committed_base"' in RUNTIME_PARITY
assert '"injectAcceptLanguage": False' in RUNTIME_PARITY
assert '"maxFetches": 18' in RUNTIME_PARITY
assert '"streams"' not in RUNTIME_PARITY.split("def sanitize", 1)[1].split("def main", 1)[0]
for route_token in ("stream", "streams", "source", "sources", "server", "servers", "resolve", "proxy", "manifest", "action"):
    assert route_token in SITE_PROBE, route_token

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
assert "mode:" in IOS and "- full" in IOS and "- only" in IOS
assert "inputs.mode != 'only'" in IOS
assert "./scripts/build-ios-ipa.sh" in IOS
assert "NIAKVIO_IOS_TARGET_PROVIDER" in IOS
assert "FIELD_NATIVE_IOS_SESSION state=warm-created" in IOS_SUITE
assert "FIELD_NATIVE_IOS_SESSION state=warm-reused" in IOS_SUITE
assert 'xcrun simctl launch --terminate-running-process' in IOS_SUITE
assert "native-mobile-ios-${{ inputs.mode == 'only' && 'only' || 'full' }}-${{ github.run_id }}" in IOS

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
