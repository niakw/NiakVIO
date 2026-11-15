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
    old_vf = root / "previous-vf.json"
    write(
        old,
        {
            "name": "NiakVIO v5.19.3",
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
        old_vf,
        {
            "name": "NiakVIO v5.19.3 — VF uniquement",
            "version": "5.19.3",
            "scrapers": [
                {
                    "id": "DEMO",
                    "name": "Demo",
                    "version": "1.0.0",
                    "filename": "../providers/demo-old.js",
                    "enabled": True,
                    "supportedTypes": ["movie"],
                },
                {
                    "id": "FRANCE-ONLY",
                    "name": "France Only",
                    "version": "3.2.1",
                    "filename": "../provider-disabled/france-only-old.js",
                    "enabled": False,
                    "supportedTypes": ["movie", "tv"],
                },
            ],
        },
    )
    write(
        root / "manifest.json",
        {
            # Simulate a generator that recreates the canonical unversioned name.
            "name": "NiakVIO",
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
            "name": "NiakVIO — VF uniquement",
            "version": "5.19.3",
            "scrapers": [
                {
                    "id": "DEMO",
                    "name": "Demo",
                    "version": "1.0.0",
                    "filename": "../providers/demo-new.js",
                    "enabled": True,
                    "supportedTypes": ["movie"],
                },
                {
                    "id": "FRANCE-ONLY",
                    "name": "France Only",
                    "version": "3.2.1",
                    "filename": "../provider-disabled/france-only-new.js",
                    "enabled": False,
                    "supportedTypes": ["movie", "tv"],
                },
            ],
        },
    )
    write(
        root / "provider-version-floors.json",
        {
            "schema_version": 1,
            "purpose": "test retained exposure floor",
            "source_commit": "test",
            "source_release": "5.19.2",
            "providers": {
                "demo": "1.0.5",
                "stable": "2.4.6",
                "france-only": "3.2.0",
            },
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
        [
            sys.executable,
            str(test_script),
            "--manifest",
            "manifest.json",
            "--previous",
            str(old),
            "--previous-vf",
            str(old_vf),
        ],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr

    current = json.loads((root / "manifest.json").read_text())
    rows = {row["id"].casefold(): row for row in current["scrapers"]}
    assert current["version"] == "5.19.4", "client-visible generation must bump global release"
    assert current["name"] == "NiakVIO v5.19.4"
    assert rows["demo"]["version"] == "1.0.6", "changed provider must recover above retained cache floor"
    assert rows["stable"]["version"] == "2.4.7", "unchanged provider must remain stable"

    vf = json.loads((root / "vf/manifest.json").read_text())
    assert vf["version"] == "5.19.4"
    assert vf["name"] == "NiakVIO v5.19.4 — VF uniquement"
    assert vf["scrapers"][0]["version"] == "1.0.6"
    assert vf["scrapers"][0]["id"] == rows["demo"]["id"]
    vf_by_id = {row["id"].casefold(): row for row in vf["scrapers"]}
    assert vf_by_id["france-only"]["version"] == "3.2.2"
    assert vf_by_id["france-only"]["filename"] == "../provider-disabled/france-only-new.js"
    assert vf_by_id["france-only"]["enabled"] is False
    assert "france-only" not in rows

    assert json.loads((root / "package.json").read_text())["version"] == "5.19.4"
    lock = json.loads((root / "package-lock.json").read_text())
    assert lock["version"] == "5.19.4"
    assert lock["packages"][""]["version"] == "5.19.4"
    sources = json.loads((root / "sources.json").read_text())
    assert sources["manifest_version"] == "5.19.4"
    assert sources["repository"]["manifest_version"] == "5.19.4"
    assert sources["repository"]["version"] == "5.19.4"
    floors = json.loads((root / "provider-version-floors.json").read_text())
    assert floors["providers"]["demo"] == "1.0.5"
    assert floors["providers"]["stable"] == "2.4.6"
    assert floors["providers"]["france-only"] == "3.2.1"

    # A second publication against the already-published generation must be a
    # complete no-op even when the generator strips the visible version before
    # finalization. The finalizer must restore it without creating a bump loop.
    previous_final = root / "previous-final.json"
    previous_final_vf = root / "previous-final-vf.json"
    previous_final.write_text((root / "manifest.json").read_text(), encoding="utf-8")
    previous_final_vf.write_text((root / "vf/manifest.json").read_text(), encoding="utf-8")
    current_before_second = json.loads((root / "manifest.json").read_text())
    current_before_second["name"] = "NiakVIO"
    write(root / "manifest.json", current_before_second)
    vf_before_second = json.loads((root / "vf/manifest.json").read_text())
    vf_before_second["name"] = "NiakVIO — VF uniquement"
    write(root / "vf/manifest.json", vf_before_second)

    result = subprocess.run(
        [
            sys.executable,
            str(test_script),
            "--manifest",
            "manifest.json",
            "--previous",
            str(previous_final),
            "--previous-vf",
            str(previous_final_vf),
        ],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    again = json.loads((root / "manifest.json").read_text())
    again_rows = {row["id"].casefold(): row for row in again["scrapers"]}
    assert again["version"] == "5.19.4"
    assert again["name"] == "NiakVIO v5.19.4"
    assert again_rows["demo"]["version"] == "1.0.6"
    assert again_rows["stable"]["version"] == "2.4.7"
    again_vf = json.loads((root / "vf/manifest.json").read_text())
    assert again_vf["name"] == "NiakVIO v5.19.4 — VF uniquement"

    # A France-only provider change is still client-visible and must bump both
    # that provider's cache version and the shared manifest release, even when
    # Global itself is byte-for-byte unchanged.
    vf_only_global = root / "previous-vf-only-global.json"
    vf_only_vf = root / "previous-vf-only-vf.json"
    vf_only_global.write_text((root / "manifest.json").read_text(), encoding="utf-8")
    vf_only_vf.write_text((root / "vf/manifest.json").read_text(), encoding="utf-8")
    vf_changed = json.loads((root / "vf/manifest.json").read_text())
    vf_changed_by_id = {row["id"].casefold(): row for row in vf_changed["scrapers"]}
    vf_changed_by_id["france-only"]["filename"] = "../provider-disabled/france-only-newer.js"
    write(root / "vf/manifest.json", vf_changed)

    result = subprocess.run(
        [
            sys.executable,
            str(test_script),
            "--manifest",
            "manifest.json",
            "--previous",
            str(vf_only_global),
            "--previous-vf",
            str(vf_only_vf),
        ],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    vf_only_final = json.loads((root / "vf/manifest.json").read_text())
    vf_only_global_final = json.loads((root / "manifest.json").read_text())
    vf_only_by_id = {row["id"].casefold(): row for row in vf_only_final["scrapers"]}
    assert vf_only_global_final["version"] == "5.19.5"
    assert vf_only_final["version"] == "5.19.5"
    assert vf_only_by_id["france-only"]["version"] == "3.2.3"
    assert vf_only_by_id["france-only"]["filename"] == "../provider-disabled/france-only-newer.js"

print("atomic release/provider cache bump tests passed")
