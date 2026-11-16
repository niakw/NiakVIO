#!/usr/bin/env python3
"""Targeted Brain staging must preserve executable Global+France identities."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import stage_published as stage  # noqa: E402


with tempfile.TemporaryDirectory(prefix="niakvio-stage-union-") as tmp_name:
    tmp = Path(tmp_name)
    global_manifest = tmp / "manifest.json"
    vf_dir = tmp / "vf"
    vf_dir.mkdir()
    france_manifest = vf_dir / "manifest.json"

    global_manifest.write_text(
        json.dumps(
            {
                "scrapers": [
                    {
                        "id": "global-one",
                        "enabled": True,
                        "filename": "providers/global-one.js",
                    },
                    {
                        "id": "shared",
                        "enabled": True,
                        "filename": "providers/shared.js",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    france_manifest.write_text(
        json.dumps(
            {
                "scrapers": [
                    {
                        "id": "shared",
                        "enabled": True,
                        "filename": "../providers/shared.js",
                    },
                    {
                        "id": "fr-only",
                        "enabled": True,
                        "filename": "../providers/fr-only.js",
                    },
                    {
                        "id": "fr-off",
                        "enabled": False,
                        "filename": "../providers/fr-off.js",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    rows = stage.targeted_projection_entries(
        {"global-one", "fr-only"},
        manifest_path=global_manifest,
        france_manifest_path=france_manifest,
    )
    by_id = {stage.canonical_id(row["id"]): row for row in rows}
    assert set(by_id) == {"global-one", "fr-only"}, by_id
    assert by_id["fr-only"]["filename"] == "providers/fr-only.js", by_id["fr-only"]

    try:
        stage.targeted_projection_entries(
            {"missing"},
            manifest_path=global_manifest,
            france_manifest_path=france_manifest,
        )
    except SystemExit as exc:
        assert "missing requested projection ids" in str(exc)
    else:
        raise AssertionError("missing targeted projection identity was silently accepted")

    try:
        stage.targeted_projection_entries(
            {"fr-off"},
            manifest_path=global_manifest,
            france_manifest_path=france_manifest,
        )
    except SystemExit as exc:
        assert "not active published Provider v3" in str(exc)
    else:
        raise AssertionError("disabled France-only provider was staged for Brain Repair")

source = (ROOT / "scripts" / "stage_published.py").read_text(encoding="utf-8")
assert "projection_rows" in source
assert 'ROOT / "vf" / "manifest.json"' in source
assert "targeted published stage failed to materialize requested ids" in source
print("targeted Brain published stage covers Global+France union and fails closed")
