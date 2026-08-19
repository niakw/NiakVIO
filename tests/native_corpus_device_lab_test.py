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

# Obsolete labs must stay removed. They used stale/mutable client refs, Linux
# Desktop as reader evidence, duplicated device work, provider-specific staging,
# or persisted overly broad runtime logs.
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

# Fast runtime retries are explicitly manual-only; they never consume runners
# because a normal provider/script push happened.
assert "workflow_dispatch:" in targeted_runtime
assert "pull_request:" not in targeted_runtime
assert "\n  push:" not in targeted_runtime
assert "run_native_corpus_tv_suite.sh" in targeted_runtime
assert "run_native_corpus_mobile_suite.sh" in targeted_runtime
assert "avd-v1-${{ runner.os }}-tv-api31-android-tv-x86-tv_1080p" in targeted_runtime
assert "avd-v1-${{ runner.os }}-mobile-api35-google_apis-x86_64-pixel_2" in targeted_runtime

# Canonical reader proof is one Android workflow: representative movie/TV/anime
# catalogue routes, every manifest provider including inactive entries, every
# returned stream, official TV/Mobile readers, then a bounded Brain retest. The
# workflow declares exhaustive intent; pull-request staging may bound that intent
# while trusted-main/manual runs keep the full path.
for fixture in ("sinners-2025", "breaking-bad-s01e01", "jujutsu-kaisen-s01e01"):
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
    "avd-v1-${{ runner.os }}-tv-api31-android-tv-x86-tv_1080p",
    "avd-v1-${{ runner.os }}-mobile-api35-google_apis-x86_64-pixel_2",
    "build_native_reader_brain_repair.py",
    "compare_native_reader_brain_repair.py",
    "--max-providers 24",
    "native-reader-brain-repair-${{ github.run_id }}",
    "native-tv-route-sinners-2025-${{ github.run_id }}",
):
    assert required in android_reader, required
assert "playback-hotfix" not in android_reader

# Desktop reader proof is native macOS/Windows only, never the Linux stub, and
# direct provider/catalog/override changes must trigger fresh native proof.
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

# Reader learning imports exactly the trusted-main Android run that completed,
# once. PR candidate evidence is diagnosable but cannot silently mutate persistent
# Brain memory. Missing repair artifacts do not consume the run id, so rerunning
# the same GitHub run remains learnable when it later produces complete evidence.
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

# Android AVDs remain warm/cached; test sessions do not save mutated snapshots.
for workflow, cache_key in (
    (android_reader, "avd-v1-${{ runner.os }}-tv-api31-android-tv-x86-tv_1080p"),
    (android_reader, "avd-v1-${{ runner.os }}-mobile-api35-google_apis-x86_64-pixel_2"),
):
    assert "actions/cache@caa296126883cff596d87d8935842f9db880ef25" in workflow
    assert cache_key in workflow
    assert "force-avd-creation: false" in workflow
    assert "-no-snapshot-save" in workflow

# Pull-request reader staging is explicitly bounded, but trusted main/manual
# execution remains exhaustive because the bound is derived from the event name.
for source, label in ((prepare_client, "prepare"), (restage_client, "restage")):
    assert "--provider" in source, (label, "target provider")
    assert "--player-probes" in source, (label, "target reader probe count")
    assert "--manifest" in source, (label, "manifest selection")
assert "raw.githubusercontent.com" in prepare_client
assert "FIELD_NATIVE_CORPUS_STAGE_SELECTED" in prepare_client
assert "GITHUB_EVENT_NAME" in restage_client
assert "NIAKVIO_PR_PROVIDER_LIMIT" in restage_client
assert "pr-bounded" in restage_client

# Official Media3 reader is primary evidence; lightweight HTTP is secondary.
for required in (
    "ExoPlayer.Builder(context)",
    "HttpDataSource.InvalidResponseCodeException",
    "PlayerPlaybackNetworking.createDataSourceFactory(context, headers)",
    "PlatformPlaybackDataSourceFactory.create(",
    "FIELD_NATIVE_PLAYER",
    "errorCodeName",
    "duration_identity",
    "short_media",
    "<redacted>",
):
    assert required in reader_codegen, required
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

# Provider/runtime anomalies are evidence. Infrastructure fails only on an
# incomplete corpus/evidence chain.
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
    f"fixtures={len(expected_slugs)} providers={len(stageable)} android_exhaustive=true desktop_native=true brain_retest=true cached_profiles=true targeted_manual=true reader_learning_idempotent=true trusted_main_learning=true missing_artifact_retriable=true pr_bounded=true"
)
