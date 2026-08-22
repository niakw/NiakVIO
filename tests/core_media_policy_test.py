#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/normalize_core_media_policy.py"
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location("core_media_policy", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

cfg = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
normalized, changed = module.normalize(cfg)
source_changes = module.normalize_source_files(apply=False)

# Once main has been normalized this must remain a pure assertion, not a repair.
assert changed == [], changed
assert source_changes == [], source_changes
module.assert_policy(normalized)

row = normalized["provider_patches"]["purstream"]
active_scripts = {str(value) for value in row.get("patch_scripts", [])}
active_options = {str(value) for value in (row.get("patch_script_options") or {})}
assert active_scripts.issubset(module.ALLOWED_SHARED_PURSTREAM_SCRIPTS), active_scripts
assert active_options.issubset(module.ALLOWED_SHARED_PURSTREAM_SCRIPTS), active_options
assert not any("purstream_" in value for value in active_scripts | active_options)

# Retired provider-specific implementations must not creep back into main.
for retired in (
    "scripts/provider_patches/purstream_tv_identity_v3.py",
    "scripts/provider_patches/purstream_tv_identity_impl_v3.py",
    "scripts/provider_patches/purstream_exact_tv_v2.py",
    "scripts/provider_patches/purstream_bridge.py",
    "scripts/migrate_tv_hardening_5_20_39.py",
):
    assert not (ROOT / retired).exists(), retired

playback = normalized["playback_integrity_policy"]
hooks = [str(value) for value in playback.get("global_discovery_hooks", [])]
assert hooks.count(module.GLOBAL_SECURITY_HOOK) == 1, hooks
assert hooks[-1] == module.GLOBAL_SECURITY_HOOK, hooks

# Prove the final reconstructed artifact, not only the configuration: a generic
# provider containing recurring unsafe shapes must leave the common Core with no
# finding, while still retaining the required provider export and presentation.
from apply_provider_overrides import apply_overrides
from provider_security_hardening import known_unsafe_findings

unsafe = b'''function badHost(u){return u.includes("example.com")};\nglobalThis.console.log("provider debug");\nglobalThis.getStreams=async function(){return []};\n'''
output, applied = apply_overrides("synthetic-core-security", unsafe, phase="discovery")
text = output.decode("utf-8")
assert known_unsafe_findings(text) == [], known_unsafe_findings(text)
assert "NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1" in text
assert "NUVIO_PROVIDER_SECURITY_HARDENING_V1" in text
assert "NUVIO_GLOBAL_STREAM_PRESENTATION_V1" in text
assert any(record.get("scope") == "global_playback_integrity" for record in applied), applied

with tempfile.NamedTemporaryFile("wb", suffix=".js", delete=False) as handle:
    handle.write(output)
    artifact = Path(handle.name)
try:
    result = subprocess.run(
        ["node", str(ROOT / "scripts/validate_provider_artifact.cjs"), str(artifact)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
finally:
    artifact.unlink(missing_ok=True)

print("Core media/security policy test passed: provider-specific media repair hooks=0; shared Core layers only")
