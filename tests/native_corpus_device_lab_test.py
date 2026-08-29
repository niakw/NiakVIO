#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
TV_READER = ROOT / ".github/workflows/native-mobile-android-reader.yml"
MOBILE_ANDROID = TV_READER
MOBILE_IOS = ROOT / ".github/workflows/native-mobile-ios-reader.yml"
PREPARE_IOS = ROOT / "scripts/prepare_native_ios_reader_acceptance.py"
DESKTOP_READER = ROOT / ".github/workflows/native-desktop-reader-acceptance.yml"
READER_LEARNING_SYNC = ROOT / ".github/workflows/native-reader-learning-sync.yml"
BRAIN_LEARNING = ROOT / ".github/workflows/brain-learning-lab.yml"
TARGETED_RUNTIME = ROOT / ".github/workflows/native-corpus-device-targeted.yml"
PREPARE_CORE = ROOT / "scripts/prepare_native_corpus_validation.py"
PREPARE_CLIENT = ROOT / "scripts/prepare_native_corpus_client.py"
RESTAGE_CLIENT = ROOT / "scripts/restage_native_corpus_client.py"
RESOLVE_REPOSITORY = ROOT / "scripts/resolve_native_repository.sh"
READER_CODEGEN = ROOT / "scripts/native_player_diagnostics_codegen.py"
READER_GATE = ROOT / "scripts/gate_native_reader_result.cjs"
MOBILE_SUITE = ROOT / "scripts/run_native_corpus_mobile_suite.sh"
TV_SUITE = ROOT / "scripts/run_native_corpus_tv_suite.sh"
COLLECTION_ANALYZER = ROOT / "scripts/analyze_native_corpus_collection.cjs"
SUMMARIZER = ROOT / "scripts/summarize_native_corpus_suite.cjs"
CORPUS = ROOT / ".github/triggers/nuvio-client-lab.json"
MANIFEST = ROOT / "manifest.json"

for retired in (
    ".github/workflows/native-android-route-reader.yml",
    ".github/workflows/native-tv-route-reader.yml",
    ".github/workflows/native-corpus-device-lab.yml",
    ".github/workflows/native-corpus-visual-sublab.yml",
    ".github/workflows/permanent-android-real-client.yml",
    ".github/workflows/permanent-real-client-labs.yml",
    ".github/workflows/nuvio-client-lab.yml",
    ".github/workflows/validate-desktop-runtime-compat.yml",
    ".github/workflows/native-desktop-stream-canary.yml",
):
    assert not (ROOT / retired).exists(), retired

tv_reader = TV_READER.read_text(encoding="utf-8")
mobile_android = MOBILE_ANDROID.read_text(encoding="utf-8")
mobile_ios = MOBILE_IOS.read_text(encoding="utf-8")
prepare_ios = PREPARE_IOS.read_text(encoding="utf-8")
desktop_reader = DESKTOP_READER.read_text(encoding="utf-8")
reader_learning = READER_LEARNING_SYNC.read_text(encoding="utf-8")
brain_learning = BRAIN_LEARNING.read_text(encoding="utf-8")
targeted_runtime = TARGETED_RUNTIME.read_text(encoding="utf-8")
prepare_core = PREPARE_CORE.read_text(encoding="utf-8")
prepare_client = PREPARE_CLIENT.read_text(encoding="utf-8")
restage_client = RESTAGE_CLIENT.read_text(encoding="utf-8")
resolve_repository = RESOLVE_REPOSITORY.read_text(encoding="utf-8")
reader_codegen = READER_CODEGEN.read_text(encoding="utf-8")
reader_gate = READER_GATE.read_text(encoding="utf-8")
mobile_suite = MOBILE_SUITE.read_text(encoding="utf-8")
tv_suite = TV_SUITE.read_text(encoding="utf-8")
collection_analyzer = COLLECTION_ANALYZER.read_text(encoding="utf-8")
summarizer = SUMMARIZER.read_text(encoding="utf-8")
corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

acceptance = corpus.get("native_reader_acceptance") or {}
assert acceptance.get("provider_scope") == "declared-type"
assert acceptance.get("one_fixture_per_type_per_provider") is True
assert acceptance.get("fixture_by_type") == {
    "movie": "interstellar",
    "tv": "breaking-bad-s01e01",
    "anime": "jujutsu-kaisen-s01e01",
}
assert corpus.get("provider_timeout_ms") == 25000
assert corpus.get("retry_provider_timeouts") is False

fixtures = "interstellar breaking-bad-s01e01 jujutsu-kaisen-s01e01"
for workflow in (tv_reader, mobile_android, desktop_reader):
    assert fixtures in workflow

for workflow in (tv_reader, mobile_android, mobile_ios, desktop_reader):
    assert "\n  pull_request:" not in workflow
    if "\n  push:" in workflow:
        assert ".github/triggers/full-native-lab-validation.json" in workflow
    assert "workflow_dispatch:" in workflow
    assert "\n  schedule:" in workflow and "cron:" in workflow

assert "matrix:" not in tv_reader
assert tv_reader.count("tv-route-reader:") == 1
assert "NIAKVIO_TARGET_FIXTURES: \"interstellar breaking-bad-s01e01 jujutsu-kaisen-s01e01\"" in tv_reader
assert "NIAKVIO_TV_PRIORITY_APPEND: \"0\"" in tv_reader
assert "NIAKVIO_TV_ROUTE_TIMEOUT_MINUTES: \"45\"" in tv_reader
assert "--streams 2" in tv_reader
assert 'NIAKVIO_PRIMARY_STREAM_SCOPE: "2"' in tv_reader
assert 'NIAKVIO_REGRESSION_STREAM_SCOPE: "2"' in tv_reader
assert "--streams all" not in tv_reader.split("\n  mobile-android-reader:", 1)[0]
assert "--streams all" in tv_reader.split("\n  mobile-android-reader:", 1)[1]
assert "native-tv-full-${{ github.run_id }}" in tv_reader

def artifact_block(workflow: str, marker: str) -> str:
    start = workflow.index(marker)
    end = workflow.find("\n      - name:", start + len(marker))
    return workflow[start:] if end < 0 else workflow[start:end]

for workflow, marker in (
    (tv_reader, 'name: native-tv-full-${{ github.run_id }}'),
    (mobile_android, 'name: native-mobile-android-full-${{ github.run_id }}'),
    (mobile_ios, "name: native-mobile-ios-${{ inputs.mode == 'only' && 'only' || 'full' }}-${{ github.run_id }}"),
    (desktop_reader, 'name: native-desktop-full-${{ matrix.os_name }}-${{ github.run_id }}'),
):
    assert "retention-days: 8" in artifact_block(workflow, marker), marker

assert "mobile-android-reader:" in mobile_android
assert "name: Native Android TV + Mobile reader acceptance" in mobile_android
assert "resolve_tv:" in mobile_android and "resolve_mobile:" in mobile_android
assert "NuvioMedia/NuvioMobile.git" in mobile_android
assert "native-mobile-android-full-${{ github.run_id }}" in mobile_android

assert "mobile-ios-reader:" in mobile_ios
assert "runs-on: macos-26" in mobile_ios
assert "DEVELOPER_DIR: /Applications/Xcode_26.6.app/Contents/Developer" in mobile_ios
assert "Build official unsigned device IPA before Lab instrumentation" in mobile_ios
assert "./scripts/build-ios-ipa.sh" in mobile_ios
assert "NIAKVIO_IOS_LAB_MODE" in mobile_ios
assert "workflow_dispatch:\n    inputs:" in mobile_ios
assert "          - full\n          - only" in mobile_ios
assert 'schedule:\n    - cron: "15 18 * * 6"' in mobile_ios
assert "NIAKVIO_IOS_TARGET_PROVIDER" in mobile_ios
assert "NIAKVIO_IOS_SESSION_STATE" in mobile_ios
assert "inputs.mode != 'only'" in mobile_ios
ios_suite = (ROOT / "scripts/run_native_corpus_ios_suite.sh").read_text(encoding="utf-8")
assert "FIELD_NATIVE_IOS_SESSION state=warm-created" in ios_suite
assert "FIELD_NATIVE_IOS_SESSION state=warm-reused" in ios_suite
assert 'MODE="${NIAKVIO_IOS_LAB_MODE:-full}"' in ios_suite
assert 'LAUNCH_RETRY_TIMEOUT_SECONDS="${NIAKVIO_IOS_LAUNCH_RETRY_TIMEOUT_SECONDS:-}"' in ios_suite
assert 'LaunchRetryTimeout -float "$LAUNCH_RETRY_TIMEOUT_SECONDS"' in ios_suite
assert 'FIELD_NATIVE_IOS_SIM_LAUNCH_TIMEOUT' in ios_suite
assert 'mode == "learning" || mode == "quick"' in prepare_ios
assert "prepare_native_ios_reader_acceptance.py" in mobile_ios
assert "run_native_corpus_ios_suite.sh" in mobile_ios
assert "analyze_native_ios_results.py" in mobile_ios
assert "native-mobile-ios-${{ inputs.mode == 'only' && 'only' || 'full' }}-${{ github.run_id }}" in mobile_ios

prepare_ios_tree = ast.parse(prepare_ios)
fixture_list_function = next(
    node for node in ast.walk(prepare_ios_tree)
    if isinstance(node, ast.FunctionDef) and node.name == "kotlin_fixture_list"
)
fixture_constants = [
    node.value for node in ast.walk(fixture_list_function)
    if isinstance(node, ast.Constant) and isinstance(node.value, str)
]
assert any("listOf(\n    " in value for value in fixture_constants), fixture_constants
assert not any("listOf(\\n    " in value for value in fixture_constants), fixture_constants

for workflow in (tv_reader, mobile_android, mobile_ios):
    assert "brain-reader-repair" not in workflow
    assert "build_native_reader_brain_repair.py" not in workflow
    assert "compare_native_reader_brain_repair.py" not in workflow
assert "workflow_run:" not in reader_learning
assert "workflow_dispatch:" in reader_learning
assert "run_id:" in reader_learning
assert "native-corpus-device-lab.yml" not in brain_learning
assert "--native-summary brain-learning-input/native-reader-summary.json" in brain_learning

assert "workflow_dispatch:" in targeted_runtime
assert "\n  push:" not in targeted_runtime
assert "\n  pull_request:" not in targeted_runtime

for source, label in ((prepare_client, "prepare"), (restage_client, "restage")):
    assert "--provider" in source, label
    assert "--player-probes" in source, label
    assert "--manifest" in source, label
prepare_tree = ast.parse(prepare_client)
hostname_guards = [
    node for node in ast.walk(prepare_tree)
    if isinstance(node, ast.Compare)
    and isinstance(node.left, ast.Attribute)
    and node.left.attr == "hostname"
    and any(isinstance(c, ast.Constant) and c.value == "raw.githubusercontent.com" for c in node.comparators)
]
assert hostname_guards
assert "FIELD_NATIVE_CORPUS_STAGE_SELECTED" in prepare_client
assert '"supportedTypes": [' in prepare_client
assert "select_declared_type" in prepare_client
assert 'mode == "declared-type"' in restage_client

for required in ("NIAKVIO_MATERIALIZE_NATIVE","source=committed-sha","https_repository_compatible=true"):
    assert required in prepare_client
pinned_assignment = next(
    line.strip() for line in resolve_repository.splitlines()
    if line.strip().startswith('NIAKVIO_RESOLVED_MANIFEST_URL="https://')
)
template = pinned_assignment.split("=",1)[1].strip().strip('"')
url = template.replace("${SOURCE_REPOSITORY}","niakw/NiakVIO").replace("${SOURCE_SHA}","0"*40).replace("${TARGET_MANIFEST}","manifest.json")
parsed = urlsplit(url)
assert parsed.scheme == "https" and parsed.hostname == "raw.githubusercontent.com"

for required in ("Screen.Player.createRoute","NuvioNavHost","LastPlaybackDiagnostics","PlatformPlayerSurface(","PlayerPlaybackSnapshot","FIELD_NATIVE_PLAYER"):
    assert required in reader_codegen
assert reader_codegen.index("val reader = probeNativePlayer") < reader_codegen.index("val transport = probeTransport")
for marker in ("no_readable_log","missing_begin_marker","incomplete_provider_traversal:"):
    assert marker in collection_analyzer

for suite, client in ((mobile_suite,"MOBILE"),(tv_suite,"TV")):
    assert 'for fixture in "${FIXTURES[@]}"' in suite, client
    assert f"FIELD_NATIVE_CORPUS_{client}_SUITE_STATUS" in suite
    assert "gate_native_reader_result.cjs" in suite

for required in ("repeatedContradictions","repeatedTransportFailures","repeatedSlow","providerRuntimeErrors","repeatedReaderFailures"):
    assert required in summarizer

stageable=[]
seen=set()
for row in manifest.get("scrapers",[]):
    if not isinstance(row,dict):
        continue
    pid=str(row.get("id") or "").strip()
    filename=str(row.get("filename") or "").strip()
    key=pid.casefold()
    if pid and filename and key not in seen:
        seen.add(key)
        stageable.append(pid)
assert len(stageable) >= 80

print(
    "native device lab contract passed: "
    f"providers={len(stageable)} type_bounded_1_1_1=true "
    "tv_single_job=true android_tv_mobile_combined=true mobile_ios_separate=true "
    "brain_decoupled=true desktop_native=true targeted_manual=true"
)
