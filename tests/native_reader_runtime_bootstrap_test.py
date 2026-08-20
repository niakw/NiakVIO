#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from augment_native_corpus_request_contract import kotlin_map  # noqa: E402
from augment_native_provider_loading import platform_set_literal, repository_helpers, tv_helpers  # noqa: E402

request_contract = (SCRIPTS / "augment_native_corpus_request_contract.py").read_text(encoding="utf-8")
provider_loading = (SCRIPTS / "augment_native_provider_loading.py").read_text(encoding="utf-8")
mobile_suite = (SCRIPTS / "run_native_corpus_mobile_suite.sh").read_text(encoding="utf-8")
desktop_workflow = (ROOT / ".github/workflows/native-desktop-reader-acceptance.yml").read_text(encoding="utf-8")

# NuvioTV's androidTest compiler must not infer nested map Pair types through
# Kotlin's generic infix `to`; the real run previously failed before the corpus
# with "Cannot infer type for type parameter T".
generated_map = kotlin_map({"provider-a": ["movie", "tv"], "provider-b": ["anime"]})
assert "mapOf<String, Set<String>>" in generated_map
assert "Pair<String, Set<String>>" in generated_map
assert " to setOf" not in generated_map
assert "Pair<String, Set<String>>" in request_contract

# The same compiler-family failure can happen in any generated empty generic.
# Keep both the literal and owning property explicitly typed so TV/Mobile/Desktop
# cannot regress when a platform happens to have zero excluded providers.
assert platform_set_literal([]) == "emptySet<String>()"
assert platform_set_literal(["provider-a"]) == 'setOf<String>("provider-a")'
tv_empty = tv_helpers("https://raw.githubusercontent.com/niakw/NiakVIO/0123456789012345678901234567890123456789/manifest.json", [])
mobile_empty = repository_helpers("mobile", "https://raw.githubusercontent.com/niakw/NiakVIO/0123456789012345678901234567890123456789/manifest.json", [])
assert "private val platformExcludedProviders: Set<String> = emptySet<String>()" in tv_empty
assert "private val platformExcludedProviders: Set<String> = emptySet<String>()" in mobile_empty
assert 'return "emptySet()"' not in provider_loading
assert "private val platformExcludedProviders =" not in provider_loading
assert "emptyMap<String, com.nuvio.tv.domain.model.ScraperInfo>()" in provider_loading
assert "emptyMap<String, PluginScraper>()" in provider_loading

# Mobile device tests execute from composeApp, but the official launcher is the
# androidApp fullDebug APK whose debug application id is com.nuviodebug.com.
assert 'packageName: String = "com.nuviodebug.com"' in request_contract
assert ":androidApp:installFullDebug" in mobile_suite
assert "adb shell pm path com.nuviodebug.com" in mobile_suite
assert "FIELD_NATIVE_MOBILE_APP_INSTALLED" in mobile_suite

# The macOS native bridge reflects into AWT peer internals. JVM module access
# must be configured before the first Gradle daemon is started, not after it.
assert "--add-opens=java.desktop/java.awt.peer=ALL-UNNAMED" in desktop_workflow
assert "--add-opens=java.desktop/sun.awt=ALL-UNNAMED" in desktop_workflow
assert 'export JAVA_TOOL_OPTIONS="$MACOS_JAVA_OPENS"' in desktop_workflow
assert desktop_workflow.index('export JAVA_TOOL_OPTIONS="$MACOS_JAVA_OPENS"') < desktop_workflow.index(":composeApp:buildMacosPlayerBridge")

print(
    "native reader runtime bootstrap contract passed: "
    "tv_explicit_pairs=true generated_empty_generics_typed=true mobile_real_app=true macos_jvm_opens_pre_gradle=true"
)
