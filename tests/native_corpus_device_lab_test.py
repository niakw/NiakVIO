#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/native-corpus-device-lab.yml"
TARGETED_WORKFLOW = ROOT / ".github/workflows/native-corpus-device-targeted.yml"
READER_WORKFLOW = ROOT / ".github/workflows/native-reader-targeted.yml"
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

workflow = WORKFLOW.read_text(encoding="utf-8")
targeted_workflow = TARGETED_WORKFLOW.read_text(encoding="utf-8")
reader_workflow = READER_WORKFLOW.read_text(encoding="utf-8")
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

# The historical full Desktop corpus remains intact. Android suites add Sinners
# because those are the real Media3 reader paths under active diagnosis.
for slug in sorted(legacy_slugs):
    assert slug in workflow, (slug, "desktop workflow")
for slug in sorted(expected_slugs):
    assert slug in mobile_suite, (slug, "mobile suite")
    assert slug in tv_suite, (slug, "tv suite")
assert "sinners-2025" in reader_workflow
assert "MOVIESDRIVE" in reader_workflow

for job in (
    "publication-gate:",
    "desktop-native-corpus:",
    "mobile-native-corpus:",
    "tv-native-corpus:",
    "native-corpus-engine-summary:",
):
    assert job in workflow, job
assert "android-mobile-tv-native-corpus:" not in workflow
assert workflow.count("runs-on: ubuntu-latest") == 5, workflow.count("runs-on: ubuntu-latest")
assert "matrix:" not in workflow
assert "strategy:" not in workflow

# Each client owns its repository/job. Mobile and TV must never share a clone or emulator job.
desktop_section = workflow.split("  desktop-native-corpus:", 1)[1].split("  mobile-native-corpus:", 1)[0]
mobile_section = workflow.split("  mobile-native-corpus:", 1)[1].split("  tv-native-corpus:", 1)[0]
tv_section = workflow.split("  tv-native-corpus:", 1)[1].split("  native-corpus-engine-summary:", 1)[0]
assert "NuvioMedia/NuvioDesktop.git" in desktop_section
assert "NuvioMedia/NuvioMobile.git" not in desktop_section
assert "NuvioMedia/NuvioTV.git" not in desktop_section
assert "NuvioMedia/NuvioMobile.git" in mobile_section
assert "NuvioMedia/NuvioTV.git" not in mobile_section
assert "NuvioMedia/NuvioDesktop.git" not in mobile_section
assert "NuvioMedia/NuvioTV.git" in tv_section
assert "NuvioMedia/NuvioMobile.git" not in tv_section
assert "NuvioMedia/NuvioDesktop.git" not in tv_section
# One cold-cache snapshot-generation invocation + one runtime invocation. Warm runs skip the first.
assert mobile_section.count("ReactiveCircus/android-emulator-runner@") == 2
assert tv_section.count("ReactiveCircus/android-emulator-runner@") == 2

# Android profiles are cached as clean snapshots and reused without saving test state.
for section, cache_key in (
    (mobile_section, "avd-v1-${{ runner.os }}-mobile-api35-google_apis-x86_64-pixel_2"),
    (tv_section, "avd-v1-${{ runner.os }}-tv-api31-android-tv-x86-tv_1080p"),
):
    assert "gradle/actions/setup-gradle@0723195856401067f7a2779048b490ace7a47d7c" in section
    assert "actions/cache@caa296126883cff596d87d8935842f9db880ef25" in section
    assert "~/.android/avd/*" in section
    assert "~/.android/adb*" in section
    assert cache_key in section
    assert section.count("force-avd-creation: false") == 2
    assert "-no-snapshot-save" in section

# TV corpus must be a genuine Android TV proof, not a phone AVD labelled as TV.
assert "api-level: 31" in tv_section
assert "target: android-tv" in tv_section
assert "arch: x86" in tv_section
assert "profile: tv_1080p" in tv_section
assert "profile: pixel_2" not in tv_section

# Existing per-device retry path remains. The reader lab is the fast human-style
# path: one established client/AVD, one fixture/provider, and 1-4 real streams.
assert "- tv\n          - mobile\n          - desktop\n          - all" in targeted_workflow
assert 'targets = [{"device": device, "fixture": "all"}]' in targeted_workflow
assert '{"device": "tv", "fixture": "all"}' in targeted_workflow
assert 'run_native_corpus_tv_suite.sh' in targeted_workflow
assert 'run-tv-targeted.sh' not in targeted_workflow
targeted_tv = targeted_workflow.split("- name: Restore TV AVD snapshot", 1)[1]
assert "api-level: 31" in targeted_tv
assert "target: android-tv" in targeted_tv
assert "arch: x86" in targeted_tv
assert "profile: tv_1080p" in targeted_tv
assert "avd-v1-${{ runner.os }}-tv-api31-android-tv-x86-tv_1080p" in targeted_tv
assert "force-avd-creation: false" in targeted_tv
assert "-no-snapshot-save" in targeted_tv
assert "run_native_corpus_mobile_suite.sh" in targeted_workflow
assert "avd-v1-${{ runner.os }}-mobile-api35-google_apis-x86_64-pixel_2" in targeted_workflow

for required in (
    "workflow_dispatch:",
    "player_probes:",
    "default: sinners-2025",
    "default: MOVIESDRIVE",
    "NIAKVIO_TARGET_FIXTURE",
    "NIAKVIO_TARGET_PROVIDER",
    "NIAKVIO_PLAYER_PROBES",
    'NIAKVIO_REQUIRE_READER_SUCCESS: "1"',
    "avd-v1-${{ runner.os }}-tv-api31-android-tv-x86-tv_1080p",
    "avd-v1-${{ runner.os }}-mobile-api35-google_apis-x86_64-pixel_2",
):
    assert required in reader_workflow, required
assert "avd-v2-" not in reader_workflow, "targeted reader lab must reuse established AVD profiles"

for required in (
    "prepare_native_corpus_client.py",
    "restage_native_corpus_client.py",
    "run_native_corpus_mobile_suite.sh",
    "run_native_corpus_tv_suite.sh",
    "analyze_native_corpus_collection.cjs",
    "summarize_native_corpus_suite.cjs",
    "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
    "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c",
):
    assert required in workflow, required

# A no-op workflow_run on another revision must not cancel a useful push corpus.
assert "native-corpus-device-lab-${{ github.event_name }}-${{ github.sha }}" in workflow
assert "workflow_run:" in workflow
assert "Niakvio provider pipeline" in workflow
assert "chore: publish validated ARCHI2 provider transaction" in workflow
assert "github.event.workflow_run.conclusion" in workflow
assert "sources.json" in workflow
assert "accepted_ref" in workflow
assert "target_sha" in workflow
assert '.github/triggers/native-corpus-device-lab' in workflow

# Provider/runtime anomalies are evidence. Only an incomplete corpus is an infrastructure failure.
assert "FIELD_NATIVE_CORPUS_BEGIN" in prepare_core
assert "FIELD_NATIVE_CORPUS_END" in prepare_core
assert "FIELD_NATIVE_ERROR" in prepare_core
for marker in (
    "no_readable_log",
    "missing_begin_marker",
    "missing_end:",
    "incomplete_provider_traversal:",
    "invalid_expected_provider_count:",
):
    assert marker in collection_analyzer, marker
assert "process.exitCode = complete ? 0 : 2" in collection_analyzer

# Kotlin/JUnit assertTrue signatures differ. Preparation and every fixture restage must preserve them.
desktop_old = 'assertTrue(errors.isEmpty(), "native provider runtime errors:'
android_old = 'assertTrue("native provider runtime errors:'
desktop_new = 'assertTrue(providers.isNotEmpty(), "native corpus provider list must not be empty")'
android_new = 'assertTrue("native corpus provider list must not be empty", providers.isNotEmpty())'
for source, label in ((prepare_client, "prepare"), (restage_client, "restage")):
    assert desktop_old in source, (label, "desktop source anchor")
    assert android_old in source, (label, "android source anchor")
    assert desktop_new in source, (label, "desktop replacement")
    assert android_new in source, (label, "android replacement")
    assert "--provider" in source, (label, "target provider")
    assert "--player-probes" in source, (label, "target reader probe count")

# Android reader diagnostics must use the official Media3 stack, not a parallel
# fake HTTP client, and expose causal errors without raw URL/credential values.
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
for required in (
    "missing_native_reader_evidence",
    "FIELD_NATIVE_READER_GATE_FAILURE",
    "readerFailureClass",
    "process.exit(failures.length ? 1 : 0)",
):
    assert required in reader_gate, required

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

# The lightweight HTTP probe remains secondary evidence for all clients.
for required in (
    "java.net.HttpURLConnection",
    "probeTransport(row.url, row.headers)",
    "#EXTM3U",
    "hlsDuration",
    "FIELD_NATIVE_TRANSPORT",
    "media_hint64",
    "host64",
):
    assert required in prepare_core, required
assert "url64=" not in prepare_core
assert "headers64=" not in prepare_core

for suite, client in ((mobile_suite, "MOBILE"), (tv_suite, "TV")):
    assert 'for fixture in "${FIXTURES[@]}"' in suite, client
    assert f"FIELD_NATIVE_CORPUS_{client}_STATUS" in suite, client
    assert f"FIELD_NATIVE_CORPUS_{client}_SUITE_STATUS" in suite, client
    assert 'NIAKVIO_REQUIRE_READER_SUCCESS' in suite, client
    assert 'gate_native_reader_result.cjs' in suite, client
    assert '--no-daemon' not in suite, client

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
assert "native-corpus-engine-summary" in workflow

print(
    "native corpus device lab coverage tests passed: "
    f"fixtures={len(expected_slugs)} stageable_providers={len(stageable)} clients=3 isolated_android_jobs=2 cached_avds=true real_tv=true targeted_reader=true reader_gate=true collection_gate=true assertion_contract=true"
)
