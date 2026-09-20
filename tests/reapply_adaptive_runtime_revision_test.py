#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


generator = load(
    "adaptive_core_generator",
    ROOT / "scripts/adaptive_runtime/runtime_recovery_generator.py",
)
current = load(
    "adaptive_v5",
    ROOT / "scripts/provider_patches/adaptive_runtime_recovery_v5.py",
)
reapply = load(
    "reapply_overrides",
    ROOT / "scripts/reapply_published_overrides.py",
)

options = {
    "provider_name": "Demo",
    "base_url": "https://demo.example",
    "types": ["movie"],
    "search_paths": ["/?s={query}"],
    "direct_paths": ["/{slug}"],
}
base = "module.exports={getStreams:async()=>[]};\n"
expected = current.apply(base, options=options)

# Synthesize a historical V4 wrapper without keeping executable V4 code in the
# repository. Reapply must accept it only as migration input and upgrade to V5.
legacy = generator.apply(base, options=options)
legacy = legacy.replace(
    "NUVIO_ADAPTIVE_RUNTIME_CORE_V7:",
    "NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V4:",
    1,
).replace(
    '"runtimeRevision":"generic-core-v3-census-focus"',
    '"runtimeRevision":"generic-core-v2"',
    1,
)
provenance = {
    "local_patches": [{
        "type": "patch_profile",
        "profile": "adaptive_runtime_recovery",
        "phase": "runtime",
        "options": options,
    }]
}

upgraded, records = reapply.reapply_adaptive_runtime_revision(legacy.encode(), provenance)
assert upgraded.decode() == expected
assert "NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V4" not in upgraded.decode()
assert records and records[0]["runtime_revision"] == "generic-core-v3"
assert records[0]["migrated_from_revision"] == 0

restored, records = reapply.reapply_adaptive_runtime_revision(base.encode(), provenance)
assert restored.decode() == expected
assert records and records[0]["runtime_revision"] == "generic-core-v3"

preserved = {
    "activation_mode": "preserved_current_ci_uncertain",
    "preserved_reason": "ci_uncertain_kept_last_published_artifact",
    "local_patches": provenance["local_patches"],
}
unchanged, records = reapply.reapply_adaptive_runtime_revision(base.encode(), preserved)
assert unchanged.decode() == base and records == []

unchanged, records = reapply.reapply_adaptive_runtime_revision(
    legacy.encode(), {"local_patches": []}
)
assert unchanged.decode() == legacy and records == []

v5_provenance = {
    "local_patches": [{
        "type": "patch_profile",
        "profile": "adaptive_runtime_recovery",
        "phase": "runtime",
        "revision": 5,
        "options": options,
    }]
}
unchanged, records = reapply.reapply_adaptive_runtime_revision(
    expected.encode(), v5_provenance
)
assert unchanged.decode() == expected and records == []

restored_v5, records = reapply.reapply_adaptive_runtime_revision(
    base.encode(), v5_provenance
)
restored_v5_text = restored_v5.decode()
assert restored_v5_text == expected
assert "NUVIO_VERIFIED_MEDIA_RUNTIME_RECOVERY_V5" in restored_v5_text
assert "NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V4" not in restored_v5_text
assert '"runtimeRevision":"generic-core-v3"' in restored_v5_text
assert records and records[0]["runtime_revision"] == "generic-core-v3"

print("adaptive runtime revision reapply test passed")
