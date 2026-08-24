#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
script_path = ROOT / "scripts" / "sync_release_versions.py"
workflow = (ROOT / ".github" / "workflows" / "sync.yml").read_text(encoding="utf-8")
script_source = script_path.read_text(encoding="utf-8")

version_call = "python scripts/sync_release_versions.py"
baseline_arg = '--previous "$NUVIO_PUBLISHED_MANIFEST_BASELINE"'
assert workflow.count(version_call) >= 2
assert "--manifest manifest.json" in workflow
assert workflow.count(baseline_arg) >= 2
assert "Capture published manifest baseline" in workflow
assert 'git show HEAD:manifest.json > "$NUVIO_PUBLISHED_MANIFEST_BASELINE"' in workflow
# Exact-published verification must use the Core-rehash-aware adapter. The
# adapter delegates to the strict legacy validator and only permits a
# deterministic content-hash/path rebinding of already-proven inert quarantine
# bundles; it does not relax activation evidence.
assert "python scripts/activation_preservation_core_rehash.py" in workflow
assert (ROOT / "scripts" / "activation_preservation_core_rehash.py").is_file()
assert "python scripts/validate_language_projection.py" in workflow
assert workflow.index(version_call) < workflow.index("python scripts/validate_language_projection.py")
assert workflow.rindex(version_call) < workflow.index("python scripts/generate_release_hashes.py")
assert "git add manifest.json vf/manifest.json provider_catalog.json" in workflow
assert "package.json package-lock.json sources.json nuvio-client-id-state.json" in workflow
assert "Verify exact published main" in workflow
assert "git diff --exit-code" in workflow
assert "auto_accept_safe_nuvio_client_heads()" in script_source
assert 'os.environ.get("GITHUB_ACTIONS") != "true"' in script_source
assert '"--apply-safe-advance"' in script_source
assert "finalize_provider_versions" in script_source
assert "resolve_release_version" in script_source

with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)
    (root / "vf").mkdir()
    (root / "package.json").write_text(json.dumps({"version": "1.0.0"}))
    (root / "package-lock.json").write_text(
        json.dumps(
            {
                "name": "nuvio-provider-health-check",
                "version": "1.0.0",
                "lockfileVersion": 3,
                "packages": {"": {"name": "nuvio-provider-health-check", "version": "1.0.0"}},
            }
        )
    )
    (root / "manifest.json").write_text(json.dumps({"version": "1.0.0", "scrapers": []}))
    (root / "vf/manifest.json").write_text(json.dumps({"version": "1.0.0", "scrapers": []}))
    (root / "sources.json").write_text(
        json.dumps(
            {
                "manifest_version": "1.0.0",
                "repository": {"manifest_version": "1.0.0", "version": "1.0.0"},
            }
        )
    )
    script = script_source.replace(
        "ROOT = pathlib.Path(__file__).resolve().parents[1]",
        f"ROOT = pathlib.Path({str(root)!r})",
    )
    test_script = root / "sync.py"
    test_script.write_text(script, encoding="utf-8")
    subprocess.run([sys.executable, str(test_script), "--version", "9.8.7"], check=True)

    assert json.loads((root / "package.json").read_text())["version"] == "9.8.7"
    lock = json.loads((root / "package-lock.json").read_text())
    assert lock["version"] == "9.8.7"
    assert lock["packages"][""]["version"] == "9.8.7"
    assert json.loads((root / "manifest.json").read_text())["version"] == "9.8.7"
    assert json.loads((root / "vf/manifest.json").read_text())["version"] == "9.8.7"
    sources = json.loads((root / "sources.json").read_text())
    assert sources["manifest_version"] == "9.8.7"
    assert sources["repository"]["manifest_version"] == "9.8.7"
    assert sources["repository"]["version"] == "9.8.7"
    assert "nuvio_client_compatibility" not in sources

print("release version synchronization test passed")
