from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

lab_workflows = {
    "android": (ROOT / ".github/workflows/native-mobile-android-reader.yml").read_text(encoding="utf-8"),
    "ios": (ROOT / ".github/workflows/native-mobile-ios-reader.yml").read_text(encoding="utf-8"),
    "desktop": (ROOT / ".github/workflows/native-desktop-reader-acceptance.yml").read_text(encoding="utf-8"),
}

request_contract = (ROOT / "scripts/augment_native_corpus_request_contract.py").read_text(encoding="utf-8")
provider_loading = (ROOT / "scripts/augment_native_provider_loading.py").read_text(encoding="utf-8")
player_diagnostics = (ROOT / "scripts/native_player_diagnostics_codegen.py").read_text(encoding="utf-8")
desktop_player = (ROOT / "scripts/augment_native_desktop_player.py").read_text(encoding="utf-8")

# Native Labs are evidence readers. Instrumentation may observe official runtime
# paths and collect diagnostics, but must never replace/rewrite provider streams,
# manufacture repaired rows, or reconstruct Provider v3 during a Lab run.
for text, label in (
    (request_contract, "request-contract"),
    (provider_loading, "provider-loading"),
    (player_diagnostics, "player-diagnostics"),
    (desktop_player, "desktop-player"),
):
    for forbidden in (
        "row.headers =",
        "row.url =",
        "rows.sorted",
        "rows.sortBy",
        "rows.sortWith",
        "copy(url =",
        "copy(headers =",
        "repairStream",
        "rewriteStream",
    ):
        assert forbidden not in text, f"{label}:{forbidden}"

# Official repository/provider state remains warm; no test-only reset to manufacture
# a different user profile or hide cache-related playback behavior.
assert "PluginRepository.clearLocalState()" not in provider_loading
assert "officialPluginManager.executeScraper(loadedScraper" in provider_loading
assert "PluginRepository.executeScraper(loadedScraper" in provider_loading

for label, workflow in lab_workflows.items():
    for forbidden in (
        "materialize_provider_v3_all.py",
        "reapply_published_overrides.py",
        "run_adaptive_deep_repair.py",
        "run_adaptive_quick_repair.py",
        "runtime_repair.py",
        "normalize_runtime_repository_dependencies.py --apply",
        "normalize_provider_rebuild_safety.py --apply",
        "normalize_core_fixed_point_contract.py --apply",
        "normalize_provider_branding_pipeline.py --apply",
        "normalize_core_media_policy.py --apply",
    ):
        assert forbidden not in workflow, f"{label} lab may not mutate/reconstruct Provider v3: {forbidden}"
assert 'NIAKVIO_ANDROID_PROVIDER_TIMEOUT_MS: "25000"' in lab_workflows["android"]
assert "NIAKVIO_IOS_PROVIDER_TIMEOUT_MS: ${{ inputs.mode == 'only' && '8000' || '25000' }}" in lab_workflows["ios"]

print("native human UX observational-purity policy and implementation tests passed")
