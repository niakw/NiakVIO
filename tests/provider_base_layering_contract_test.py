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
# Legacy current provider logic may already contain idempotent source-level
# security normalization. It is not a Core/routing/quarantine layer.
module.assert_base_layering(
    b"/* NUVIO_PROVIDER_SECURITY_HARDENING_V1:legacy */\n" + valid,
    "synthetic-security-normalized",
)

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

assert module.CLEAN_RECONSTRUCTION_SOURCE == "niakvio-clean-reconstruction-v2"
assert module.CLEAN_RECONSTRUCTION_AUTHORING_VERSION == 2
assert module.requires_clean_reconstruction({}) is True
for old_source in (
    "one-shot-public-core-tail-extraction",
    "provider-pipeline-legacy-rebase",
    "selected_candidate_post_provider_overrides_pre_core",
    "niakvio-clean-reconstruction",
):
    assert module.requires_clean_reconstruction({
        "base_source": old_source,
        "clean_reconstruction_verified": True,
        "clean_reconstruction_authoring_version": 1,
    }) is True

clean_row = {
    "base_source": "niakvio-clean-reconstruction-v2",
    "clean_reconstruction_verified": True,
    "clean_reconstruction_authoring_version": 2,
}
assert module.is_clean_reconstructed(clean_row) is True
assert module.requires_clean_reconstruction(clean_row) is False

assert module.QUARANTINE_PATCH in module.DERIVED_PATCH_SCRIPTS
assert module.DYNAMIC_DOMAIN_PATCH in module.DERIVED_PATCH_SCRIPTS
assert "scripts/provider_patches/adaptive_runtime_recovery_v5.py" in module.DERIVED_PATCH_SCRIPTS
assert "scripts/provider_patches/adaptive_domain_recovery.py" in module.DERIVED_PATCH_SCRIPTS

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

assert "materialize_provider_v3_all.py" in manual_workflow_source
assert "verify_provider_v3_reverse_rebuild.py" in manual_workflow_source
assert "python scripts/provider_base_store.py validate" in manual_workflow_source
assert "def repair_derived_base_tails()" in base_store_source

print("ProviderBase layering contract tests passed")
