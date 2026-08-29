#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "provider_base_store.py"

spec = importlib.util.spec_from_file_location("provider_base_store_layering", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

required = {
    "NUVIO_PROVIDER_QUARANTINE_V1",
    "NUVIO_GLOBAL_CORE_START_BOUNDARY_V1",
    "NUVIO_GLOBAL_STREAM_PRESENTATION_V1",
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

for marker in sorted(required):
    contaminated = (f"/* {marker} */\n").encode() + valid
    try:
        module.assert_base_layering(contaminated, "synthetic")
    except ValueError as exc:
        assert marker in str(exc), (marker, exc)
    else:
        raise AssertionError(f"derived marker accepted in ProviderBase: {marker}")

assert set(module.LEGACY_LOCAL_SEEDS) == {
    "cineby", "cinemm", "goatapi", "toflix", "4khdhubnew"
}

assert module.QUARANTINE_PATCH in module.DERIVED_PATCH_SCRIPTS
assert module.DYNAMIC_DOMAIN_PATCH in module.DERIVED_PATCH_SCRIPTS
assert "scripts/provider_patches/adaptive_runtime_recovery_v5.py" in module.DERIVED_PATCH_SCRIPTS
assert "scripts/provider_patches/adaptive_domain_recovery.py" in module.DERIVED_PATCH_SCRIPTS

apply_source = (ROOT / "scripts" / "apply_provider_overrides.py").read_text(encoding="utf-8")
promoter_source = (ROOT / "scripts" / "promote_candidates.py").read_text(encoding="utf-8")
workflow_source = (ROOT / ".github" / "workflows" / "core-media-finalize-main.yml").read_text(encoding="utf-8")

assert "excluded_patch_scripts: Iterable[str] | None = None" in apply_source
assert "if patch_script in excluded_scripts:" in apply_source
assert "persist_base_from_seed" in promoter_source
assert "previous_base_row" in promoter_source
assert "python scripts/provider_base_store.py repair-legacy" in workflow_source
assert workflow_source.index("python scripts/provider_base_store.py repair-legacy") < workflow_source.index(
    "python scripts/provider_base_store.py validate"
)

print("ProviderBase layering contract tests passed")
