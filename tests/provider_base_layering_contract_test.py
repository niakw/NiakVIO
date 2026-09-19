#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "provider_base_store.py"
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location("provider_base_store_layering", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

required = {
    "NUVIO_PROVIDER_SECURITY_HARDENING_V1",
    "NUVIO_PROVIDER_QUARANTINE_V1",
    "NUVIO_GLOBAL_CORE_START_BOUNDARY_V1",
    "NUVIO_GLOBAL_STREAM_PRESENTATION_V1",
    "NUVIO_STREAM_OUTPUT_SANITIZER_V4",
    "NUVIO_STREAM_OUTPUT_SANITIZER_UTF8_BOM_V5",
    "NUVIO_STREAM_OUTPUT_SANITIZER_ALL_URL_FAIL_CLOSED_V6",
    "NUVIO_GLOBAL_MEDIA_TYPE_RESOLUTION_V1",
    "NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1",
    "NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1",
    "NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1",
    "NUVIO_RUNTIME_REPOSITORY_DOMAIN_MATERIALIZER_V1",
}
assert required <= set(module.DERIVED_BASE_MARKERS)

valid = b"module.exports={getStreams:async()=>[]};\n"
module.assert_base_layering(valid, "synthetic")

# Security hardening is a publication/composed layer. It must never be accepted
# as a seed for the clean common ProviderBase.
security_contaminated = b"/* NUVIO_PROVIDER_SECURITY_HARDENING_V1:legacy */\n" + valid
try:
    module.assert_base_layering(security_contaminated, "synthetic-security-normalized")
except ValueError as exc:
    assert "NUVIO_PROVIDER_SECURITY_HARDENING_V1" in str(exc), exc
else:
    raise AssertionError("security hardening derived layer accepted in clean ProviderBase")

contaminated_tail = (
    valid
    + b"/* NUVIO_STREAM_OUTPUT_SANITIZER_V4:fixture */\n"
    + b";(function(g,c){g.__derived=true})(globalThis,{});\n"
)
cleaned_tail, stripped_tail = module.clean_base_from_published("synthetic-tail", contaminated_tail)
assert stripped_tail is True
assert cleaned_tail == valid.rstrip()
module.assert_base_layering(cleaned_tail, "synthetic-tail")

for marker in sorted(required):
    contaminated = (f"/* {marker} */\n").encode() + valid
    try:
        module.assert_base_layering(contaminated, "synthetic")
    except ValueError as exc:
        assert marker in str(exc), (marker, exc)
    else:
        raise AssertionError(f"derived marker accepted in ProviderBase: {marker}")

adaptive_fixture = """const keep=true;
/* NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V4:deadbeef */
;(function(g,c){g.__derived=true})(typeof globalThis!==\"undefined\"?globalThis:this,{\"x\":1});
const after=true;
"""
adaptive_clean, adaptive_count = module.strip_adaptive_runtime_wrappers(adaptive_fixture)
assert adaptive_count == 1
assert "NUVIO_ADAPTIVE_RUNTIME_RECOVERY" not in adaptive_clean
assert "const keep=true;" in adaptive_clean and "const after=true;" in adaptive_clean

v5_fixture = """const keep=true;
/* NUVIO_VERIFIED_MEDIA_RUNTIME_RECOVERY_V5:deadbeef */
;(function(g,c){g.__derived=true})(typeof globalThis!==\"undefined\"?globalThis:this,{\"x\":1});
"""
v5_clean, v5_count = module.strip_adaptive_runtime_wrappers(v5_fixture)
assert v5_count == 1
assert "NUVIO_VERIFIED_MEDIA_RUNTIME_RECOVERY_V5" not in v5_clean
assert "const keep=true;" in v5_clean

# Clean reconstruction authority is v3. Older clean-v1/v2 provenance must be
# rematerialized rather than silently treated as current.
assert module.CLEAN_RECONSTRUCTION_SOURCE == "niakvio-clean-reconstruction-v3"
assert module.CLEAN_RECONSTRUCTION_AUTHORING_VERSION >= 3
assert module.PROVIDER_BASE_OWNED_MARKER == "NIAKVIO_PROVIDER_BASE_OWNED_V3"
assert module.requires_clean_reconstruction({}) is True
for old_source, old_authoring in (
    ("one-shot-public-core-tail-extraction", 1),
    ("provider-pipeline-legacy-rebase", 1),
    ("selected_candidate_post_provider_overrides_pre_core", 1),
    ("niakvio-clean-reconstruction", 1),
    ("niakvio-clean-reconstruction-v2", 2),
):
    assert module.requires_clean_reconstruction({
        "base_source": old_source,
        "clean_reconstruction_verified": True,
        "clean_reconstruction_authoring_version": old_authoring,
    }) is True

clean_row = {
    "base_source": module.CLEAN_RECONSTRUCTION_SOURCE,
    "clean_reconstruction_verified": True,
    "clean_reconstruction_authoring_version": module.CLEAN_RECONSTRUCTION_AUTHORING_VERSION,
}
assert module.is_clean_reconstructed(clean_row) is True
assert module.requires_clean_reconstruction(clean_row) is False

# Only quarantine remains a derived patch script in the clean-v3 patch surface.
# Historical runtime/domain materializers are read-only legacy source paths and
# are explicitly excluded from reconstruction rather than replayed.
assert module.DERIVED_PATCH_SCRIPTS == {module.QUARANTINE_PATCH}
for legacy_path in (
    "scripts/provider_patches/runtime_repository_domain_materializer_v1.py",
    "scripts/provider_patches/adaptive_domain_recovery.py",
    "scripts/provider_patches/adaptive_runtime_recovery_v5.py",
):
    assert legacy_path in module.LEGACY_SOURCE_PATCH_PATHS, legacy_path
    assert legacy_path in module.CLEAN_RECONSTRUCTION_EXCLUDED_PATCH_SCRIPTS, legacy_path
    assert legacy_path not in module.DERIVED_PATCH_SCRIPTS, legacy_path

apply_source = (ROOT / "scripts" / "apply_provider_overrides.py").read_text(encoding="utf-8")
manual_workflow_source = (ROOT / ".github" / "workflows" / "provider-v3-reconstruct-all.yml").read_text(encoding="utf-8")
routine_workflow_source = (ROOT / ".github" / "workflows" / "sync.yml").read_text(encoding="utf-8")

assert "excluded_patch_scripts: Iterable[str] | None = None" in apply_source
assert "include_global_core: bool = True" in apply_source
assert "GLOBAL_MEDIA_TYPE_RESOLUTION" in apply_source
assert '"scope": "global_media_type_resolution"' in apply_source
assert 'if phase == "discovery" and include_global_core:' in apply_source
base_store_source = SCRIPT.read_text(encoding="utf-8")
for forbidden_seed_path in (
    "def _snapshot_seed(",
    "def _git_seed(",
    "def _pre_hardening_git_seed(",
    "def _latest_snapshot_seed(",
    "def _persist_recovery_fallback(",
):
    assert forbidden_seed_path not in base_store_source, forbidden_seed_path
assert "migrate-existing is disabled" in base_store_source
assert "published_legacy_code_may_seed_new_base" in base_store_source
assert '"published_legacy_code_may_seed_new_base": False' in base_store_source
assert '"upstream_code_may_seed_new_base": False' in base_store_source
assert '"git_history_code_may_seed_new_base": False' in base_store_source
assert "include_global_core=False" in base_store_source
assert "if patch_script in excluded_scripts:" in apply_source

for forbidden in (
    "repair-legacy",
    "repair-derived",
    "materialize_provider_v3_all.py",
    "verify_provider_v3_reverse_rebuild.py",
):
    assert forbidden not in routine_workflow_source, forbidden

assert "materialize_provider_base_v3_store.py" in manual_workflow_source
assert "materialize_provider_v3_all.py" in manual_workflow_source
assert "verify_provider_v3_reverse_rebuild.py" in manual_workflow_source
assert "python scripts/provider_base_store.py validate" in manual_workflow_source
assert "def repair_derived_base_tails()" in base_store_source

print("ProviderBase layering contract tests passed")