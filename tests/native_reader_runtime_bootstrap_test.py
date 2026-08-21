#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from augment_native_corpus_request_contract import kotlin_map  # noqa: E402
from augment_native_provider_loading import insert_imports, platform_set_literal, repository_helpers, tv_helpers  # noqa: E402
from native_player_diagnostics_codegen import TV_IMPORTS  # noqa: E402
from nuvio_tv_test_bootstrap import enable_tv_tests  # noqa: E402

request_contract = (SCRIPTS / "augment_native_corpus_request_contract.py").read_text(encoding="utf-8")
provider_loading = (SCRIPTS / "augment_native_provider_loading.py").read_text(encoding="utf-8")
mobile_suite = (SCRIPTS / "run_native_corpus_mobile_suite.sh").read_text(encoding="utf-8")
desktop_suite = (SCRIPTS / "run_native_corpus_desktop_suite.sh").read_text(encoding="utf-8")
desktop_player = (SCRIPTS / "augment_native_desktop_player.py").read_text(encoding="utf-8")
desktop_workflow = (ROOT / ".github/workflows/native-desktop-reader-acceptance.yml").read_text(encoding="utf-8")
tv_bootstrap = (SCRIPTS / "nuvio_tv_test_bootstrap.py").read_text(encoding="utf-8")
reader_acceptance = (SCRIPTS / "prepare_native_reader_acceptance.py").read_text(encoding="utf-8")
corpus_client = (SCRIPTS / "prepare_native_corpus_client.py").read_text(encoding="utf-8")

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

# Player and repository augmentation are two layers of one generated TV test.
# Repository loading owns their shared Hilt/Flow imports; the player layer must
# never emit a second copy (the official 0.8.7 Kotlin compiler rejects duplicates).
layered_tv_imports = insert_imports(
    "import androidx.test.platform.app.InstrumentationRegistry\n" + TV_IMPORTS,
    "tv",
)
for shared_import in (
    "import dagger.hilt.EntryPoint\n",
    "import dagger.hilt.InstallIn\n",
    "import dagger.hilt.android.EntryPointAccessors\n",
    "import dagger.hilt.components.SingletonComponent\n",
    "import kotlinx.coroutines.flow.first\n",
):
    assert shared_import not in TV_IMPORTS, shared_import
    assert layered_tv_imports.count(shared_import) == 1, shared_import

# NuvioTV instrumentation bootstrap is a structural contract, never a client
# version contract. The official client advanced from 0.8.4 to 0.8.7 and exposed
# why anchoring on versionName was wrong. Future version bumps must remain valid.
assert 'versionName = "0.8.4-beta"' not in tv_bootstrap
assert "defaultConfig" in tv_bootstrap
assert "enable_tv_test_bootstrap(repo)" in reader_acceptance
assert "enable_tv_test_bootstrap(tv)" in corpus_client
assert "corpus.enable_tv_tests" not in reader_acceptance
assert "corpus.enable_tv_tests" not in corpus_client
with tempfile.TemporaryDirectory(prefix="niakvio-tv-bootstrap-") as tmp:
    repo = Path(tmp)
    build = repo / "app/build.gradle.kts"
    build.parent.mkdir(parents=True)
    build.write_text(
        '''android {\n    defaultConfig {\n        applicationId = "com.nuvio.tv"\n        versionCode = 9999\n        versionName = "9.99.0-future"\n    }\n    buildTypes {\n        debug {\n            signingConfig = signingConfigs.getByName("release")\n        }\n    }\n}\n''',
        encoding="utf-8",
    )
    enable_tv_tests(repo)
    first = build.read_text(encoding="utf-8")
    enable_tv_tests(repo)
    second = build.read_text(encoding="utf-8")
    assert second == first
    assert first.count('testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"') == 1
    assert first.count('androidTestImplementation("androidx.test.ext:junit:1.3.0")') == 1
    assert first.count('androidTestImplementation("androidx.test:runner:1.7.0")') == 1
    assert 'signingConfigs.getByName("debug")' in first
    assert 'versionName = "9.99.0-future"' in first

# Mobile device tests execute from composeApp, but the official launcher is the
# androidApp fullDebug APK whose debug application id is com.nuviodebug.com.
assert 'packageName: String = "com.nuviodebug.com"' in request_contract
assert ":androidApp:installFullDebug" in mobile_suite
assert "adb shell pm path com.nuviodebug.com" in mobile_suite
assert "FIELD_NATIVE_MOBILE_APP_INSTALLED" in mobile_suite

# Desktop evidence must run under the same ordinary JVM/module policy and
# composition-local contract as the real NuvioDesktop UI. The current production
# PlatformPlayerSurface reads LocalNuvioPlatformDensity, which is intentionally
# unavailable outside NuvioTheme; a bare ComposePanel is therefore not production.
for forbidden in (
    "--add-opens=java.desktop/java.awt.peer=ALL-UNNAMED",
    "--add-opens=java.desktop/sun.awt=ALL-UNNAMED",
    "MACOS_JAVA_OPENS",
    "JAVA_TOOL_OPTIONS",
):
    assert forbidden not in desktop_workflow, forbidden
assert "No test-only --add-opens/JVM privilege relaxation" in desktop_workflow
assert "root_execution_forbidden" in desktop_suite
assert "privilege=ordinary-user" in desktop_suite
assert "import com.nuvio.app.core.ui.NuvioTheme" in desktop_player
assert "NuvioTheme {" in desktop_player
assert "desktopThrowableChain" in desktop_player
assert "exception_chain64=${{b64(reader.exceptionChain)}}" in desktop_player

print(
    "native reader runtime bootstrap contract passed: "
    "tv_explicit_pairs=true generated_empty_generics_typed=true tv_single_owner_hilt_imports=true "
    "tv_version_agnostic_bootstrap=true mobile_real_app=true desktop_ordinary_jvm_policy=true "
    "desktop_production_theme=true desktop_unwrapped_errors=true"
)
