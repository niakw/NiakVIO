#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_language_projection.py"

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    vf_dir = root / "vf"
    vf_dir.mkdir()
    no_anime_dir = root / "no-anime"
    no_anime_dir.mkdir()
    vf_no_anime_dir = root / "vf-no-anime"
    vf_no_anime_dir.mkdir()

    manifest = {
        "name": "Projection fixture",
        "version": "1.2.3",
        "scrapers": [
            {
                "id": "declared-fr",
                "filename": "providers/declared-fr.js",
                "contentLanguage": ["fr"],
                "enabled": True,
                "supportedTypes": ["movie", "tv"],
            },
            {
                "id": "anime-only",
                "filename": "providers/anime-only.js",
                "contentLanguage": ["fr"],
                "supportedTypes": ["anime"],
                "enabled": True,
            },
            {
                # Mixed type stays in no-anime when the provider identity itself
                # does not advertise anime.
                "id": "OBSERVED-VF",
                "filename": "providers/observed-vf.js",
                "contentLanguage": ["en"],
                "supportedTypes": ["movie", "anime"],
                "enabled": True,
            },
            {
                # A mixed provider whose id/name identifies it as anime-oriented
                # is intentionally excluded by the no-anime projection.
                "id": "ANIMEXTRA",
                "name": "Anime Extra",
                "filename": "providers/animextra.js",
                "contentLanguage": ["fr"],
                "supportedTypes": ["movie", "tv", "anime"],
                "enabled": True,
            },
            {
                "id": "english-only",
                "filename": "providers/english-only.js",
                "contentLanguage": ["en"],
                "supportedTypes": ["movie"],
                "enabled": True,
            },
        ],
    }
    report = {
        "providers": [
            {"id": "declared-fr", "manifest_ordering": {"language_group": "other"}},
            {"id": "anime-only", "manifest_ordering": {"language_group": "vf"}},
            {"id": "observed-vf", "manifest_ordering": {"language_group": "vf"}},
            {"id": "animextra", "manifest_ordering": {"language_group": "vf"}},
            {"id": "english-only", "manifest_ordering": {"language_group": "other"}},
        ]
    }
    expected_vf = {
        "name": "Projection fixture — VF uniquement",
        "version": "1.2.3",
        "scrapers": [
            {
                "id": "declared-fr",
                "filename": "../providers/declared-fr.js",
                "contentLanguage": ["fr"],
                "enabled": True,
                "supportedTypes": ["movie", "tv"],
            },
            {
                "id": "anime-only",
                "filename": "../providers/anime-only.js",
                "contentLanguage": ["fr"],
                "supportedTypes": ["anime"],
                "enabled": True,
            },
            {
                "id": "OBSERVED-VF",
                "filename": "../providers/observed-vf.js",
                "contentLanguage": ["en"],
                "supportedTypes": ["movie", "anime"],
                "enabled": True,
            },
            {
                "id": "ANIMEXTRA",
                "name": "Anime Extra",
                "filename": "../providers/animextra.js",
                "contentLanguage": ["fr"],
                "supportedTypes": ["movie", "tv", "anime"],
                "enabled": True,
            },
        ],
    }

    manifest_path = root / "manifest.json"
    report_path = root / "health-report.json"
    vf_path = vf_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    report_path.write_text(json.dumps(report), encoding="utf-8")
    vf_path.write_text(json.dumps(expected_vf), encoding="utf-8")

    def excluded(row):
        values = [str(v).strip().casefold() for v in row.get("supportedTypes", []) if str(v).strip()]
        anime_only = bool(values) and set(values) == {"anime"}
        identity = " ".join(str(row.get(key) or "").casefold() for key in ("id", "name"))
        return anime_only or "anim" in identity

    expected_no_anime = {
        "name": "Projection fixture — Without anime providers",
        "version": "1.2.3",
        "scrapers": [
            {**row, "filename": "../" + row["filename"]}
            for row in manifest["scrapers"]
            if not excluded(row)
        ],
    }
    expected_vf_no_anime = {
        "name": "Projection fixture — VF uniquement — Without anime providers",
        "version": "1.2.3",
        "scrapers": [row for row in expected_vf["scrapers"] if not excluded(row)],
    }
    no_anime_path = no_anime_dir / "manifest.json"
    vf_no_anime_path = vf_no_anime_dir / "manifest.json"
    no_anime_path.write_text(json.dumps(expected_no_anime), encoding="utf-8")
    vf_no_anime_path.write_text(json.dumps(expected_vf_no_anime), encoding="utf-8")

    command = [
        sys.executable,
        str(VALIDATOR),
        "--manifest",
        str(manifest_path),
        "--report",
        str(report_path),
        "--vf",
        str(vf_path),
        "--no-anime",
        str(no_anime_path),
        "--vf-no-anime",
        str(vf_no_anime_path),
    ]
    result = subprocess.run(command, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VF projection validation passed" in result.stdout

    # Mixed movie/anime stays when identity is neutral; anim-named mixed row does not.
    actual_no_anime = json.loads(no_anime_path.read_text(encoding="utf-8"))
    no_anime_ids = {str(row.get("id")) for row in actual_no_anime["scrapers"]}
    assert "OBSERVED-VF" in no_anime_ids
    assert "anime-only" not in no_anime_ids
    assert "ANIMEXTRA" not in no_anime_ids

    # Any semantic drift in the nested projection is publication-blocking.
    tampered = json.loads(json.dumps(expected_vf))
    tampered["scrapers"][1]["enabled"] = False
    vf_path.write_text(json.dumps(tampered), encoding="utf-8")
    result = subprocess.run(command, text=True, capture_output=True)
    assert result.returncode == 1
    assert "VF projection validation failed" in result.stderr

    # Order is part of the curated manifest contract as well.
    reordered = json.loads(json.dumps(expected_vf))
    reordered["scrapers"].reverse()
    vf_path.write_text(json.dumps(reordered), encoding="utf-8")
    result = subprocess.run(command, text=True, capture_output=True)
    assert result.returncode == 1
    assert "order_mismatch=True" in result.stderr

print("VF/no-anime language projection tests passed")
