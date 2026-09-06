#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
script_path = ROOT / "scripts" / "sync_release_versions.py"
baseline_path = ROOT / "scripts" / "release_version_baseline.py"
workflow_path = ROOT / ".github" / "workflows" / "release-finalize.yml"
workflow = workflow_path.read_text(encoding="utf-8")
script_source = script_path.read_text(encoding="utf-8")
baseline_source = baseline_path.read_text(encoding="utf-8")

# Accepted-release finalization is explicit and exact-SHA-bound. The routine
# Verify & Publish workflow must not silently bump cache/release versions before
# the native/provider validation pile has been accepted.
assert "name: CORE - Finalize Accepted Release" in workflow
assert "workflow_dispatch:" in workflow
assert "expected_sha:" in workflow
assert 'test "$ACTUAL" = "${{ inputs.expected_sha }}"' in workflow
assert "python3 scripts/release_version_baseline.py" in workflow
assert "python3 scripts/sync_release_versions.py" in workflow
assert '--previous "$RUNNER_TEMP/published-manifest-baseline.json"' in workflow
assert workflow.index("python3 scripts/sync_release_versions.py") < workflow.index("python3 scripts/generate_release_hashes.py")
assert workflow.index("python3 scripts/generate_release_hashes.py") < workflow.index("python3 scripts/validate_release_integrity.py")
assert "Verify bounded finalization diff" in workflow
assert "git push origin HEAD:main" in workflow
assert "--first-parent" in baseline_source
assert "current_version" in baseline_source
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
    (root / "provider_catalog.json").write_text(
        json.dumps(
            {
                "manifestMeta": {
                    "general": {"name": "General", "version": "1.0.0"},
                    "vf": {"name": "VF", "version": "1.0.0"},
                }
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
    catalog = json.loads((root / "provider_catalog.json").read_text())
    assert catalog["manifestMeta"]["general"]["version"] == "9.8.7"
    assert catalog["manifestMeta"]["vf"]["version"] == "9.8.7"
    assert "nuvio_client_compatibility" not in sources

print("release version synchronization test passed")
