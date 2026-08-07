#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
script_path = ROOT / "scripts" / "sync_release_versions.py"
workflow = (ROOT / ".github/workflows/sync.yml").read_text(encoding="utf-8")
assert "python scripts/sync_release_versions.py --manifest manifest.json" in workflow
assert "python scripts/validate_activation_preservation.py" in workflow
assert "python scripts/validate_language_projection.py" in workflow
assert workflow.index("python scripts/sync_release_versions.py --manifest manifest.json") < workflow.index("python scripts/validate_language_projection.py")
assert workflow.index("python scripts/validate_language_projection.py") < workflow.index("python scripts/generate_release_hashes.py")
assert "git add manifest.json vf/manifest.json package.json package-lock.json sources.json" in workflow

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
    script = script_path.read_text(encoding="utf-8").replace(
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

print("release version synchronization test passed")
