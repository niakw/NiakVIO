#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETED_RUNTIME = ROOT / ".github/workflows/native-corpus-device-targeted.yml"
ANDROID_READER = ROOT / ".github/workflows/native-android-route-reader.yml"
DESKTOP_READER = ROOT / ".github/workflows/native-desktop-reader-acceptance.yml"
READER_LEARNING_SYNC = ROOT / ".github/workflows/native-reader-learning-sync.yml"
BRAIN_LEARNING = ROOT / ".github/workflows/brain-learning-lab.yml"
PREPARE_CORE = ROOT / "scripts/prepare_native_corpus_validation.py"
PREPARE_CLIENT = ROOT / "scripts/prepare_native_corpus_client.py"
RESTAGE_CLIENT = ROOT / "scripts/restage_native_corpus_client.py"
READER_CODEGEN = ROOT / "scripts/native_player_diagnostics_codegen.py"
READER_GATE = ROOT / "scripts/gate_native_reader_result.cjs"
MOBILE_SUITE = ROOT / "scripts/run_native_corpus_mobile_suite.sh"
TV_SUITE = ROOT / "scripts/run_native_corpus_tv_suite.sh"
COLLECTION_ANALYZER = ROOT / "scripts/analyze_native_corpus_collection.cjs"
SUMMARIZER = ROOT / "scripts/summarize_native_corpus_suite.cjs"
CORPUS = ROOT / ".github/triggers/nuvio-client-lab.json"
MANIFEST = ROOT / "manifest.json"

for retired in (
    ".github/workflows/native-corpus-device-lab.yml",
    ".github/workflows/native-corpus-visual-sublab.yml",
    ".github/workflows/permanent-android-real-client.yml",
    ".github/workflows/permanent-real-client-labs.yml",
    ".github/workflows/nuvio-client-lab.yml",
    ".github/workflows/validate-desktop-runtime-compat.yml",
):
    assert not (ROOT / retired).exists(), retired

targeted_runtime = TARGETED_RUNTIME.read_text(encoding="utf-8")
android_reader = ANDROID_READER.read_text(encoding="utf-8")
desktop_reader = DESKTOP_READER.read_text(encoding="utf-8")
reader_learning = READER_LEARNING_SYNC.read_text(encoding="utf-8")
brain_learning = BRAIN_LEARNING.read_text(encoding="utf-8")
prepare_core = PREPARE_CORE.read_text(encoding="utf-8")
prepare_client = PREPARE_CLIENT.read_text(encoding="utf-8")
restage_client = RESTAGE_CLIENT.read_text(encoding="utf-8")
reader_codegen = READER_CODEGEN.read_text(encoding="utf-8")
reader_gate = READER_GATE.read_text(encoding="utf-8")
mobile_suite = MOBILE_SUITE.read_text(encoding="utf-8")
tv_suite = TV_SUITE.read_text(encoding="utf-8")
collection_analyzer = COLLECTION_ANALYZER.read_text(encoding="utf-8")
summarizer = SUMMARIZER.read_text(encoding="utf-8")
corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

legacy_slugs = {
    "interstellar",
    "mon-ninja-et-moi-3",
    "breaking-bad-s01e01",
    "revenant-s01e01",
    "jujutsu-kaisen-s01e01",
    "mushoku-tensei-s01e01",
}
expected_slugs = legacy_slugs | {"sinners-2025"}
actual_slugs = {
    str(row.get("slug") or "")
    for row in corpus.get("fixtures", [])
    if isinstance(row, dict)
}
assert actual_slugs == expected_slugs, (actual_slugs, expected_slugs)

# Manual targeted retries remain manual-only and must never reuse an AVD from a
# different NiakVIO/client generation.
assert "workflow_dispatch:" in targeted_runtime
assert "pull_request:" not in targeted_runtime
assert "\n  push:" not in targeted_runtime
assert "run_native_corpus_tv_suite.sh" in targeted_runtime
assert "run_native_corpus_mobile_suite.sh" in targeted_runtime
assert "avd-v1-" not in targeted_runtime
for required in (
    "avd-v2-${{ runner.os }}-tv-api31-android-tv-x86-tv_1080p-${{ needs.resolve.outputs.tv_sha }}-${{ github.sha }}",
    "avd-v2-${{ runner.os }}-mobile-api35-google_apis-x86_64-pixel_2-${{ needs.resolve.outputs.mobile_sha }}-${{ github.sha }}",
):
    assert required in targeted_runtime, required

# Canonical Android proof uses current official client SHAs and a runtime
# fingerprint in every persistent AVD cache key. No broad restore fallback exists.
representative_fixtures = ("sinners-2025", "breaking-bad-s01e01", "jujutsu-kaisen-s01e01")
for fixture in representative_fixtures:
    assert fixture in android_reader, fixture
for required in (
    "pull_request:",
    "push:",
    '      - "providers/**"',
    '      - "provider_catalog.json"',
    '      - "provider-overrides.json"',
    '      - "vf/manifest.json"',
    "NuvioMedia/NuvioTV.git",
    "NuvioMedia/NuvioMobile.git",
    "NIAKVIO_TARGET_PROVIDER: all",
    "NIAKVIO_PRIMARY_STREAM_SCOPE: all",
    "NIAKVIO_REGRESSION_STREAM_SCOPE: all",
    "--provider all --streams all",
    'NIAKVIO_REQUIRE_READER_SUCCESS: "1"',
    "avd-v2-${{ runner.os }}-tv-api31-android-tv-x86-tv_1080p-${{ needs.resolve.outputs.tv_sha }}-${{ needs.resolve.outputs.runtime_fingerprint }}",
    "avd-v2-${{ runner.os }}-mobile-api35-google_apis-x86_64-pixel_2-${{ needs.resolve.outputs.mobile_sha }}-${{ needs.resolve.outputs.runtime_fingerprint }}",
    "build_native_reader_brain_repair.py",
    "compare_native_reader_brain_repair.py",
    "--max-providers 24",
    "native-reader-brain-repair-${{ github.run_id }}",
    "native-tv-route-representative-${{ github.run_id }}",
    "native-mobile-route-representative-${{ github.run_id }}",
    "representative-cross-client-brain.json",
    "tv-reader-repair-comparison-${fixture}.json",
    "Re-read every provider and returned stream for all representative routes after Brain mutation",
):
    assert required in android_reader, required
assert android_reader.count('NIAKVIO_TARGET_FIXTURES: "sinners-2025 breaking-bad-s01e01 jujutsu-kaisen-s01e01"') >= 3
assert "avd-v1-" not in android_reader
assert "restore-keys:" not in android_reader
assert "playback-hotfix" not in android_reader

# Android AVD sessions are cacheable, while every actual test boot remains
# non-persistent so a failed playback cannot poison the saved clean generation.
for workflow in (android_reader, targeted_runtime):
    assert "actions/cache@caa296126883cff596d87d8935842f9db880ef25" in workflow
    assert "force-avd-creation: false" in workflow
    assert "-no-snapshot-save" in workflow

# Desktop proof remains real macOS/Windows native player evidence.
for required in (
    "macos-15",
    "windows-2022",
    '      - "providers/**"',
    '      - "provider_catalog.json"',
    '      - "provider-overrides.json"',
    '      - "vf/manifest.json"',
    "NuvioMedia/NuvioDesktop.git",
    ":composeApp:buildMacosPlayerBridge",
    ":composeApp:buildWindowsPlayerBridge",
    "Microsoft.Web.WebView2",
    "NIAKVIO_TARGET_PROVIDER: all",
    "NIAKVIO_PRIMARY_STREAM_SCOPE: all",
    "NIAKVIO_REGRESSION_STREAM_SCOPE: all",
    "native-evidence/desktop/**",
):
    assert required in desktop_reader, required
assert "official_nuvio_desktop_player_is_stub" in (ROOT / "scripts/run_native_corpus_desktop_suite.sh").read_text(encoding="utf-8")

# Learning is trusted-main only and idempotent.
for required in (
    "Native Android route reader acceptance",
    "github.event.workflow_run.id",
    "github.event.workflow_run.event == 'push'",
    "github.event.workflow_run.head_branch == 'main'",
    "importedRunIds",
    "native-reader-brain-repair-$RUN_ID",
    "has_comparison=true",
    "has_comparison=false",
    "steps.source.outputs.repair_duplicate != 'true'",
    "rm -rf reader-learning-input/acceptance",
    "duplicate",
):
    assert required in reader_learning, required
assert "NiakVIO Brain learning lab" not in reader_learning
assert "gh run list --workflow native-android-route-reader.yml" not in reader_learning
assert "native-corpus-device-lab.yml" not in brain_learning
assert "--native-summary" not in brain_learning
assert "--provider-portfolio" not in brain_learning
assert "nativeReaderRepairMemory" in brain_learning

# PR staging is bounded; trusted main/manual paths retain exhaustive intent.
for source, label in ((prepare_client, "prepare"), (restage_client, "restage")):
    assert "--provider" in source, (label, "target provider")
    assert "--player-probes" in source, (label, "target reader probe count")
    assert "--manifest" in source, (label, "manifest selection")
assert "raw.githubusercontent.com" in prepare_client
assert "FIELD_NATIVE_CORPUS_STAGE_SELECTED" in prepare_client
assert "GITHUB_EVENT_NAME" in restage_client
assert "NIAKVIO_PR_PROVIDER_LIMIT" in restage_client
assert "pr-bounded" in restage_client

# The production Nuvio player is primary evidence; transport probing comes after it.
for required in (
    "Screen.Player.createRoute",
    "NuvioNavHost",
    "LastPlaybackDiagnostics",
    "PlatformPlayerSurface(",
    "PlayerPlaybackSnapshot",
    "nuvio-tv-production",
    "nuvio-mobile-production",
    "FIELD_NATIVE_PLAYER",
    "duration_identity",
    "short_media",
    "<redacted>",
):
    assert required in reader_codegen, required
for forbidden in (
    "ExoPlayer.Builder(context)",
    "PlayerPlaybackNetworking.createDataSourceFactory(context, headers)",
    "PlatformPlaybackDataSourceFactory.create(",
):
    assert forbidden not in reader_codegen, forbidden
assert reader_codegen.index("val reader = probeNativePlayer") < reader_codegen.index("val transport = probeTransport")
for required in (
    "missing_native_reader_evidence",
    "FIELD_NATIVE_READER_GATE_FAILURE",
    "readerFailureClass",
    "process.exit(failures.length ? 1 : 0)",
):
    assert required in reader_gate, required
for required in (
    "java.net.HttpURLConnection",
    "probeTransport(row.url, row.headers)",
    "#EXTM3U",
    "FIELD_NATIVE_TRANSPORT",
):
    assert required in prepare_core, required
assert "url64=" not in prepare_core
assert "headers64=" not in prepare_core

# Collection integrity stays strict; provider/playback outcomes are evidence.
for marker in (
    "no_readable_log",
    "missing_begin_marker",
    "missing_end:",
    "incomplete_provider_traversal:",
    "invalid_expected_provider_count:",
):
    assert marker in collection_analyzer, marker
assert "process.exitCode = complete ? 0 : 2" in collection_analyzer

for suite, client in ((mobile_suite, "MOBILE"), (tv_suite, "TV")):
    assert 'for fixture in "${FIXTURES[@]}"' in suite, client
    assert f"FIELD_NATIVE_CORPUS_{client}_STATUS" in suite, client
    assert f"FIELD_NATIVE_CORPUS_{client}_SUITE_STATUS" in suite, client
    assert "NIAKVIO_REQUIRE_READER_SUCCESS" in suite, client
    assert "NIAKVIO_TARGET_MANIFEST" in suite, client
    assert '--manifest "$TARGET_MANIFEST"' in suite, client
    assert "gate_native_reader_result.cjs" in suite, client
    assert "--no-daemon" not in suite, client

for required in (
    "repeatedContradictions",
    "repeatedTransportFailures",
    "repeatedSlow",
    "repeatedPlatformGaps",
    "systemicEmpty",
    "providerRuntimeErrors",
    "repeatedReaderFailures",
    "nativeReaderFailures",
    "readerFailureClasses",
    "FIELD_NATIVE_ENGINE_SIGNAL",
):
    assert required in summarizer, required

stageable = []
seen = set()
for row in manifest.get("scrapers", []):
    if not isinstance(row, dict):
        continue
    provider_id = str(row.get("id") or "").strip()
    filename = str(row.get("filename") or "").strip()
    key = provider_id.casefold()
    if not provider_id or not filename or key in seen:
        continue
    seen.add(key)
    stageable.append(provider_id)
assert len(stageable) >= 80, len(stageable)

print(
    "native device lab contract passed: "
    f"fixtures={len(expected_slugs)} providers={len(stageable)} android_exhaustive=true "
    "desktop_native=true brain_retest=movie-tv-anime cached_profiles=v2-fingerprinted "
    "targeted_manual=true reader_learning_idempotent=true trusted_main_learning=true "
    "missing_artifact_retriable=true pr_bounded=true production_player_only=true"
)
