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
assert "highest_historical_release" in script_source
assert "release downgrade rejected" in script_source


def write_release_fixture(root: pathlib.Path, version: str) -> None:
    (root / "vf").mkdir(exist_ok=True)
    (root / "no-anime").mkdir(exist_ok=True)
    (root / "vf-no-anime").mkdir(exist_ok=True)
    (root / "package.json").write_text(json.dumps({"version": version}))
    (root / "package-lock.json").write_text(
        json.dumps(
            {
                "name": "nuvio-provider-health-check",
                "version": version,
                "lockfileVersion": 3,
                "packages": {"": {"name": "nuvio-provider-health-check", "version": version}},
            }
        )
    )
    manifest = {"name": "NiakVIO", "version": version, "scrapers": []}
    (root / "manifest.json").write_text(json.dumps(manifest))
    (root / "vf/manifest.json").write_text(json.dumps({"name": "NiakVIO — VF uniquement", "version": version, "scrapers": []}))
    (root / "no-anime/manifest.json").write_text(json.dumps({"name": "NiakVIO — Without anime providers", "version": version, "scrapers": []}))
    (root / "vf-no-anime/manifest.json").write_text(json.dumps({"name": "NiakVIO — VF uniquement — Without anime providers", "version": version, "scrapers": []}))
    (root / "sources.json").write_text(
        json.dumps(
            {
                "manifest_version": version,
                "repository": {"manifest_version": version, "version": version},
            }
        )
    )
    (root / "provider_catalog.json").write_text(
        json.dumps(
            {
                "manifestMeta": {
                    "general": {"name": "General", "version": version},
                    "vf": {"name": "VF", "version": version},
                }
            }
        )
    )


with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)
    write_release_fixture(root, "1.0.0")
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
    assert json.loads((root / "manifest.json").read_text())["name"] == "NiakVIO v9.8.7"
    assert json.loads((root / "vf/manifest.json").read_text())["name"] == "NiakVIO v9.8.7 — VF uniquement"
    sources = json.loads((root / "sources.json").read_text())
    assert sources["manifest_version"] == "9.8.7"
    assert sources["repository"]["manifest_version"] == "9.8.7"
    assert sources["repository"]["version"] == "9.8.7"
    catalog = json.loads((root / "provider_catalog.json").read_text())
    assert catalog["manifestMeta"]["general"]["version"] == "9.8.7"
    assert catalog["manifestMeta"]["vf"]["version"] == "9.8.7"
    assert "nuvio_client_compatibility" not in sources

# Regression lock for the real failure mode that occurred during the main
# consolidation: a previously published 5.21.39 must never become 5.21.37.
with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)
    write_release_fixture(root, "5.21.39")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "NiakVIO Test"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "published 5.21.39"], cwd=root, check=True)

    write_release_fixture(root, "5.21.37")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "regressed merge bytes"], cwd=root, check=True)

    script = script_source.replace(
        "ROOT = pathlib.Path(__file__).resolve().parents[1]",
        f"ROOT = pathlib.Path({str(root)!r})",
    )
    test_script = root / "sync.py"
    test_script.write_text(script, encoding="utf-8")

    rejected = subprocess.run(
        [sys.executable, str(test_script), "--version", "5.21.38"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert rejected.returncode != 0
    assert "historical_floor=5.21.39" in (rejected.stdout + rejected.stderr)

    previous = root / "previous.json"
    previous.write_text(json.dumps({"name": "NiakVIO", "version": "5.21.37", "scrapers": []}))
    current = json.loads((root / "manifest.json").read_text())
    current["description"] = "new provider generation"
    (root / "manifest.json").write_text(json.dumps(current))
    subprocess.run(
        [sys.executable, str(test_script), "--manifest", "manifest.json", "--previous", str(previous)],
        check=True,
    )
    assert json.loads((root / "manifest.json").read_text())["version"] == "5.21.40"
    assert json.loads((root / "package.json").read_text())["version"] == "5.21.40"
    assert json.loads((root / "vf/manifest.json").read_text())["version"] == "5.21.40"
    assert json.loads((root / "manifest.json").read_text())["name"] == "NiakVIO v5.21.40"

print("release version synchronization test passed")
