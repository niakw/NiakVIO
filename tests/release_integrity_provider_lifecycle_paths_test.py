#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_release_integrity as integrity  # noqa: E402


def write_json(path: pathlib.Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def row(provider_id: str, filename: str, *, enabled: bool = True) -> dict:
    return {"id": provider_id, "filename": filename, "enabled": enabled}


with tempfile.TemporaryDirectory() as directory:
    temp = pathlib.Path(directory)
    old_root = integrity.ROOT
    integrity.ROOT = temp
    try:
        (temp / "providers").mkdir()
        (temp / "provider-disabled").mkdir()
        (temp / "vf").mkdir()
        (temp / "providers" / "active.js").write_text("active\n", encoding="utf-8")
        (temp / "provider-disabled" / "disabled.js").write_text("disabled\n", encoding="utf-8")

        write_json(temp / "manifest.json", {
            "scrapers": [
                row("active", "providers/active.js"),
                row("disabled", "provider-disabled/disabled.js", enabled=False),
            ]
        })
        assert integrity.validate_manifest_paths("manifest.json", nested=False) == []

        write_json(temp / "vf" / "manifest.json", {
            "scrapers": [
                row("active", "../providers/active.js"),
                row("disabled", "../provider-disabled/disabled.js", enabled=False),
            ]
        })
        assert integrity.validate_manifest_paths("vf/manifest.json", nested=True) == []

        write_json(temp / "manifest.json", {
            "scrapers": [row("active", "provider-disabled/disabled.js")]
        })
        errors = integrity.validate_manifest_paths("manifest.json", nested=False)
        assert any("active filename must start providers/" in value for value in errors), errors

        write_json(temp / "manifest.json", {
            "scrapers": [row("disabled", "providers/active.js", enabled=False)]
        })
        errors = integrity.validate_manifest_paths("manifest.json", nested=False)
        assert any("disabled filename must start provider-disabled/" in value for value in errors), errors

        write_json(temp / "manifest.json", {
            "scrapers": [row("disabled", "provider-disabled/disabled.js", enabled=False)]
        })
        errors = integrity.validate_manifest_paths("manifest.json", nested=False, allow_disabled=False)
        assert errors == ["manifest.json:disabled: disabled provider is forbidden in active-only manifest"], errors

        write_json(temp / "manifest.json", {
            "scrapers": [row("disabled", "provider-disabled/../providers/active.js", enabled=False)]
        })
        errors = integrity.validate_manifest_paths("manifest.json", nested=False)
        assert any("escapes provider-disabled/ lifecycle scope" in value for value in errors), errors
    finally:
        integrity.ROOT = old_root

print("release integrity provider lifecycle path tests passed")
