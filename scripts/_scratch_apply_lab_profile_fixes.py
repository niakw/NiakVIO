#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


# Repository request markers are useful when exposed passively, but no longer
# mandatory after Nuvio runtime HTTP instrumentation was deliberately forbidden.
path = "scripts/native_evidence_completeness.cjs"
text = read(path)
old = '''    // Cache hits legitimately produce no repository network traffic. A successful
    // fresh install must prove its manifest/provider HTTP chain. A terminal install
    // failure may occur before a request is constructed; that absence is itself
    // valid evidence when the structured load error and provider fallout are present.
    if (!scope.repositoryLoadFailed && scope.repositoryLoadBegun > 0 && scope.repositoryCacheHits === 0 && scope.repositoryHttpRequests === 0) {
      problems.push(`missing_repository_http:${label}`);
    }
'''
new = '''    // Repository HTTP markers are passive diagnostics only. Runtime HTTP
    // instrumentation is forbidden by the human-UX policy, so a successful
    // repository load/result plus provider-load coverage is sufficient proof even
    // when the official client exposes no request-level marker. If a passive request
    // is observed, its terminal response/error remains mandatory below.
'''
text = replace_once(text, old, new, path)
write(path, text)

path = "tests/native_evidence_completeness_test.cjs"
text = read(path)
anchor = "  console.log('native evidence completeness execution-floor tests passed');\n"
addition = r'''  const passiveFresh = writeLog(tmp, 'passive-fresh.log', baseEvidence([
    'FIELD_NATIVE_PROVIDER_BEGIN client=tv fixture=sinners-2025 provider=test request_type=movie',
    'FIELD_NATIVE_RESULT client=tv fixture=sinners-2025 provider=test request_type=movie enabled=true count=0',
  ], [
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=provider-loading',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=provider-result',
  ]).filter((line) => !line.startsWith('FIELD_NATIVE_REPOSITORY_CACHE_HIT ')));
  const passiveFreshAssessment = assessNativeEvidence([passiveFresh]);
  assert.equal(
    passiveFreshAssessment.complete,
    true,
    `passive successful repository evidence must not require injected HTTP markers: ${JSON.stringify(passiveFreshAssessment.problems)}`,
  );
  assert.ok(!passiveFreshAssessment.problems.some((problem) => problem.startsWith('missing_repository_http:')));

  const missingRepositoryTerminal = writeLog(tmp, 'missing-repository-terminal.log', baseEvidence([
    'FIELD_NATIVE_PROVIDER_BEGIN client=tv fixture=sinners-2025 provider=test request_type=movie',
    'FIELD_NATIVE_RESULT client=tv fixture=sinners-2025 provider=test request_type=movie enabled=true count=0',
  ], [
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=provider-loading',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=provider-result',
  ]).filter((line) => !line.startsWith('FIELD_NATIVE_REPOSITORY_LOAD_RESULT ')));
  const missingRepositoryTerminalAssessment = assessNativeEvidence([missingRepositoryTerminal]);
  assert.equal(missingRepositoryTerminalAssessment.complete, false);
  assert.ok(missingRepositoryTerminalAssessment.problems.some((problem) => problem.startsWith('repository_load_terminal:tv:sinners-2025:0/1')));

  console.log('native evidence completeness execution-floor tests passed');
'''
text = replace_once(text, anchor, addition, path)
write(path, text)

# Mobile device-test JNI package collision + TV debug-only Hilt entrypoint.
path = "scripts/native_client_test_bootstrap.py"
text = read(path)
text = text.replace(
    "runner, test dependencies, and (for TV) a debug signing configuration required\n"
    "to install the debug APK on the emulator.  It must never change production\n"
    "Android manifests, networking policy, player code, stream headers, storage,\n"
    "DNS, proxying, decoder settings, or any other runtime behaviour.",
    "runner, test dependencies, device-test packaging, and (for TV) a debug signing\n"
    "configuration/debug-only Hilt entry point required to install and exercise the debug\n"
    "APK on the emulator. It must never change production Android manifests, networking\n"
    "policy, player code, stream headers, storage, DNS, proxying, decoder settings, or\n"
    "any other production runtime behaviour.",
)
mobile_anchor = '''    build.write_text(text, encoding="utf-8")
    print("FIELD_NATIVE_TEST_BOOTSTRAP client=mobile scope=test-only runtime_mutation=false")
'''
mobile_new = '''    # The device-test APK merges JNI payloads from both mpv-android-lib and
    # ass-media. Both legitimately ship libc++_shared.so; the KMP Android plugin
    # otherwise aborts mergeAndroidDeviceTestNativeLibs before the emulator starts.
    # pickFirst is package assembly only: it preserves both runtime dependencies and
    # does not modify production source, player, network or OS policy.
    if 'variant.packaging.jniLibs.pickFirsts.add("**/libc++_shared.so")' not in text:
        text = text.rstrip() + """

androidComponents {
    onVariants { variant ->
        variant.packaging.jniLibs.pickFirsts.add("**/libc++_shared.so")
    }
}
"""
    build.write_text(text, encoding="utf-8")
    print("FIELD_NATIVE_TEST_BOOTSTRAP client=mobile scope=test-only packaging=libcxx-pick-first runtime_mutation=false")
'''
text = replace_once(text, mobile_anchor, mobile_new, path)
tv_anchor = '''    build.write_text(text, encoding="utf-8")
    print("FIELD_NATIVE_TEST_BOOTSTRAP client=tv scope=test-only runtime_mutation=false")
'''
tv_new = '''    build.write_text(text, encoding="utf-8")

    # Hilt cannot aggregate an @EntryPoint declared only inside androidTest into the
    # application SingletonComponent. Put the diagnostic accessor in the ephemeral
    # debug source set so Hilt generates it into the debug app graph. This file never
    # exists in upstream and is absent from release/production source sets.
    entrypoint = Path(repo) / "app/src/debug/java/com/nuvio/tv/core/plugin/NiakvioLabPluginManagerEntryPoint.kt"
    entrypoint.parent.mkdir(parents=True, exist_ok=True)
    entrypoint.write_text(
        """package com.nuvio.tv.core.plugin

import dagger.hilt.EntryPoint
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent

@EntryPoint
@InstallIn(SingletonComponent::class)
interface NiakvioLabPluginManagerEntryPoint {
    fun pluginManager(): PluginManager
}
""",
        encoding="utf-8",
    )
    print("FIELD_NATIVE_TEST_BOOTSTRAP client=tv scope=test-only hilt_entrypoint=debug-source runtime_mutation=false")
'''
text = replace_once(text, tv_anchor, tv_new, path)
write(path, text)

path = "scripts/augment_native_provider_loading.py"
text = read(path)
old = '''    shared_imports = (
        "import dagger.hilt.EntryPoint\\n",
        "import dagger.hilt.InstallIn\\n",
        "import dagger.hilt.android.EntryPointAccessors\\n",
        "import dagger.hilt.components.SingletonComponent\\n",
        "import kotlinx.coroutines.flow.first\\n",
    )
'''
new = '''    shared_imports = (
        "import dagger.hilt.android.EntryPointAccessors\\n",
        "import kotlinx.coroutines.flow.first\\n",
    )
'''
text = replace_once(text, old, new, path)
old = '''    @EntryPoint
    @InstallIn(SingletonComponent::class)
    interface NiakvioPluginManagerEntryPoint {{
        fun pluginManager(): PluginManager
    }}

'''
text = replace_once(text, old, "", path)
text = text.replace("NiakvioPluginManagerEntryPoint::class.java", "NiakvioLabPluginManagerEntryPoint::class.java")
write(path, text)

# Persist the fixes so future runs reuse them instead of re-diagnosing them.
path = "automation/native-human-ux-policy.json"
data = json.loads(read(path))
data["version"] = 5
data["persistent_profiles"]["schema_version"] = 2

tv = data["persistent_profiles"]["tv"]
tv_item = "app/src/debug/java/com/nuvio/tv/core/plugin/NiakvioLabPluginManagerEntryPoint.kt (ephemeral debug-only Hilt accessor)"
if tv_item not in tv["allowed_test_plumbing"]:
    tv["allowed_test_plumbing"].append(tv_item)
tv["hilt_entrypoint_profile"] = "debug-source entry point aggregated into the ephemeral debug app Hilt graph; never declare the required PluginManager entry point only inside androidTest"

mobile = data["persistent_profiles"]["mobile"]
mobile_item = "device-test JNI packaging pickFirst for **/libc++_shared.so when duplicate STL payloads block mergeAndroidDeviceTestNativeLibs"
if mobile_item not in mobile["allowed_test_plumbing"]:
    mobile["allowed_test_plumbing"].append(mobile_item)
mobile["jni_packaging_profile"] = "preserve mpv and ass-media dependencies; resolve duplicate libc++_shared.so only in ephemeral test-checkout packaging via KotlinMultiplatformAndroid variant packaging"

entries = {row["id"]: row for row in data["job_blocker_memory"]["entries"]}
entries["repository-http-evidence-gap-after-instrumentation-disable"].update({
    "status": "resolved",
    "cause": "completeness incorrectly treated passive repository HTTP markers as mandatory after runtime instrumentation was intentionally disabled",
    "resolution": "repository load begin/result plus provider-load coverage is sufficient; HTTP request/terminal markers are optional passive diagnostics and are paired only when observed",
    "never_repeat": "do not re-enable Nuvio repository/network runtime instrumentation and do not require synthetic repository HTTP markers",
})
for row in (
    {
        "id": "tv-androidtest-hilt-entrypoint-not-aggregated",
        "status": "resolved",
        "signature": "ClassCastException DaggerNuvioApplication_HiltComponents_SingletonC$SingletonCImpl to NiakvioNativeCorpusTvTest$NiakvioPluginManagerEntryPoint",
        "cause": "Hilt entry point declared only inside androidTest was not aggregated into the application SingletonComponent",
        "resolution": "create a debug-source-only NiakvioLabPluginManagerEntryPoint in the ephemeral checkout and make androidTest access PluginManager through that app-compiled entry point",
        "never_repeat": "do not declare required Hilt application entry points only inside androidTest and do not patch Nuvio production Hilt modules",
    },
    {
        "id": "mobile-device-test-libcxx-shared-duplicate",
        "status": "resolved",
        "signature": "mergeAndroidDeviceTestNativeLibs duplicate libc++_shared.so from mpv-android-lib and ass-media",
        "cause": "the device-test APK packaging merges two legitimate native dependencies that both carry libc++_shared.so",
        "resolution": "use KotlinMultiplatform Android variant test-checkout packaging pickFirst for **/libc++_shared.so while preserving both runtime dependencies",
        "never_repeat": "do not exclude mpv/ass-media and do not change production player dependencies to make device-test packaging green",
    },
):
    existing = entries.get(row["id"])
    if existing is None:
        data["job_blocker_memory"]["entries"].append(row)
    else:
        existing.update(row)

checkout_item = "app/src/debug/java/com/nuvio/tv/core/plugin/NiakvioLabPluginManagerEntryPoint.kt"
if checkout_item not in data["allowed_checkout_changes"]["tv"]:
    data["allowed_checkout_changes"]["tv"].append(checkout_item)
gradle_item = 'variant.packaging.jniLibs.pickFirsts.add("**/libc++_shared.so")'
if gradle_item not in data["allowed_gradle_additions"]["mobile"]:
    data["allowed_gradle_additions"]["mobile"].append(gradle_item)
for intent in (
    "resolve a device-test-only native library packaging collision without excluding production player dependencies",
    "add a debug-source-only Hilt entry point when application graph aggregation is required for diagnostic instrumentation",
):
    if intent not in data["allowed_change_intent"]:
        data["allowed_change_intent"].append(intent)
write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")

path = "tests/native_human_ux_policy_lock_test.py"
text = read(path)
text = text.replace('assert POLICY["version"] >= 4', 'assert POLICY["version"] >= 5')
text = text.replace('assert profiles["schema_version"] == 1', 'assert profiles["schema_version"] >= 2')
text = text.replace(
    '    "actions-log-blob-not-ready",\n):',
    '    "actions-log-blob-not-ready",\n    "tv-androidtest-hilt-entrypoint-not-aggregated",\n    "mobile-device-test-libcxx-shared-duplicate",\n):',
)
text = text.replace(
    '    "stale-tv-bootstrap-alias-contract",\n):',
    '    "stale-tv-bootstrap-alias-contract",\n    "repository-http-evidence-gap-after-instrumentation-disable",\n    "tv-androidtest-hilt-entrypoint-not-aggregated",\n    "mobile-device-test-libcxx-shared-duplicate",\n):',
)
old = '''assert entries["repository-http-evidence-gap-after-instrumentation-disable"]["status"] == "watch"
assert "never restore Nuvio runtime HTTP instrumentation" in entries["repository-http-evidence-gap-after-instrumentation-disable"]["next_action"]
'''
new = '''assert entries["repository-http-evidence-gap-after-instrumentation-disable"]["status"] == "resolved"
assert "do not re-enable Nuvio repository/network runtime instrumentation" in entries["repository-http-evidence-gap-after-instrumentation-disable"]["never_repeat"]
assert entries["tv-androidtest-hilt-entrypoint-not-aggregated"]["status"] == "resolved"
assert "debug-source-only" in entries["tv-androidtest-hilt-entrypoint-not-aggregated"]["resolution"]
assert entries["mobile-device-test-libcxx-shared-duplicate"]["status"] == "resolved"
assert "pickFirst" in entries["mobile-device-test-libcxx-shared-duplicate"]["resolution"]
assert "NiakvioLabPluginManagerEntryPoint" in profiles["tv"]["hilt_entrypoint_profile"]
assert "libc++_shared.so" in profiles["mobile"]["jni_packaging_profile"]
'''
text = replace_once(text, old, new, path)
write(path, text)

path = "tests/native_reader_runtime_bootstrap_test.py"
text = read(path)
old = '''for shared_import in (
    "import dagger.hilt.EntryPoint\\n",
    "import dagger.hilt.InstallIn\\n",
    "import dagger.hilt.android.EntryPointAccessors\\n",
    "import dagger.hilt.components.SingletonComponent\\n",
    "import kotlinx.coroutines.flow.first\\n",
):
'''
new = '''for shared_import in (
    "import dagger.hilt.android.EntryPointAccessors\\n",
    "import kotlinx.coroutines.flow.first\\n",
):
'''
text = replace_once(text, old, new, path)
text = text.replace(
    'assert "emptyMap<String, com.nuvio.tv.domain.model.ScraperInfo>()" in provider_loading',
    'assert "emptyMap<String, com.nuvio.tv.domain.model.ScraperInfo>()" in provider_loading\nassert "NiakvioLabPluginManagerEntryPoint::class.java" in provider_loading\nassert "interface NiakvioPluginManagerEntryPoint" not in provider_loading',
)
needle = '''    assert 'versionName = "9.99.0-future"' in first
'''
replacement = '''    assert 'versionName = "9.99.0-future"' in first
    debug_entrypoint = repo / "app/src/debug/java/com/nuvio/tv/core/plugin/NiakvioLabPluginManagerEntryPoint.kt"
    assert debug_entrypoint.is_file()
    debug_text = debug_entrypoint.read_text(encoding="utf-8")
    assert "@EntryPoint" in debug_text
    assert "@InstallIn(SingletonComponent::class)" in debug_text
    assert "fun pluginManager(): PluginManager" in debug_text
'''
text = replace_once(text, needle, replacement, path)
write(path, text)

print("FIELD_SCRATCH_PATCH lab_profile_fixes=applied")
