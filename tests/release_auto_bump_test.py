#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
script_source = (ROOT / "scripts" / "sync_release_versions.py").read_text(encoding="utf-8")


def write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / "vf").mkdir()

    old = root / "previous.json"
    write(
        old,
        {
            "name": "x",
            "version": "5.19.3",
            "scrapers": [
                {
                    "id": "DEMO",
                    "name": "Demo",
                    "version": "1.0.0",
                    "filename": "providers/demo-old.js",
                    "enabled": True,
                    "supportedTypes": ["movie"],
                },
                {
                    "id": "STABLE",
                    "name": "Stable",
                    "version": "2.4.7",
                    "filename": "providers/stable.js",
                    "enabled": True,
                    "supportedTypes": ["movie"],
                },
            ],
        },
    )
    write(
        root / "manifest.json",
        {
            "name": "x",
            "version": "5.19.3",
            "scrapers": [
                {
                    "id": "DEMO",
                    "name": "Demo",
                    "version": "1.0.0",
                    "filename": "providers/demo-new.js",
                    "enabled": True,
                    "supportedTypes": ["movie"],
                },
                {
                    "id": "STABLE",
                    "name": "Stable",
                    "version": "2.4.7",
                    "filename": "providers/stable.js",
                    "enabled": True,
                    "supportedTypes": ["movie"],
                },
            ],
        },
    )
    write(
        root / "vf/manifest.json",
        {
            "name": "x-vf",
            "version": "5.19.3",
            "scrapers": [
                {
                    "id": "DEMO",
                    "name": "Demo",
                    "version": "1.0.0",
                    "filename": "../providers/demo-new.js",
                    "enabled": True,
                    "supportedTypes": ["movie"],
                }
            ],
        },
    )
    write(root / "package.json", {"version": "5.19.3"})
    write(
        root / "package-lock.json",
        {
            "name": "nuvio-provider-health-check",
            "version": "5.19.3",
            "lockfileVersion": 3,
            "packages": {"": {"name": "nuvio-provider-health-check", "version": "5.19.3"}},
        },
    )
    write(
        root / "sources.json",
        {
            "manifest_version": "5.19.3",
            "repository": {"manifest_version": "5.19.3", "version": "5.19.3"},
        },
    )

    script = script_source.replace(
        "ROOT = pathlib.Path(__file__).resolve().parents[1]",
        f"ROOT = pathlib.Path({str(root)!r})",
    )
    test_script = root / "sync.py"
    test_script.write_text(script, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(test_script), "--manifest", "manifest.json", "--previous", str(old)],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr

    current = json.loads((root / "manifest.json").read_text())
    rows = {row["id"].casefold(): row for row in current["scrapers"]}
    assert current["version"] == "5.19.4", "client-visible generation must bump global release"
    assert rows["demo"]["version"] == "1.0.1", "changed provider must bump its own cache version"
    assert rows["stable"]["version"] == "2.4.7", "unchanged provider must remain stable"

    vf = json.loads((root / "vf/manifest.json").read_text())
    assert vf["version"] == "5.19.4"
    assert vf["scrapers"][0]["version"] == "1.0.1"
    assert vf["scrapers"][0]["id"] == rows["demo"]["id"]

    assert json.loads((root / "package.json").read_text())["version"] == "5.19.4"
    lock = json.loads((root / "package-lock.json").read_text())
    assert lock["version"] == "5.19.4"
    assert lock["packages"][""]["version"] == "5.19.4"
    sources = json.loads((root / "sources.json").read_text())
    assert sources["manifest_version"] == "5.19.4"
    assert sources["repository"]["manifest_version"] == "5.19.4"
    assert sources["repository"]["version"] == "5.19.4"

    # A second publication against the already-published generation must be a
    # complete no-op: no global bump and no provider bump loop.
    previous_final = root / "previous-final.json"
    previous_final.write_text((root / "manifest.json").read_text(), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(test_script), "--manifest", "manifest.json", "--previous", str(previous_final)],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    again = json.loads((root / "manifest.json").read_text())
    again_rows = {row["id"].casefold(): row for row in again["scrapers"]}
    assert again["version"] == "5.19.4"
    assert again_rows["demo"]["version"] == "1.0.1"
    assert again_rows["stable"]["version"] == "2.4.7"

print("atomic release/provider cache bump tests passed")
