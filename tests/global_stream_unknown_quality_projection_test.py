#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

upgrade_path = ROOT / "scripts" / "upgrade_stream_presentation_unknown_quality_v1.py"
spec = importlib.util.spec_from_file_location("upgrade_stream_presentation_unknown_quality_v1_test", upgrade_path)
assert spec and spec.loader
upgrade = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upgrade)
upgrade.patch()
upgrade.validate()

presentation_path = ROOT / "scripts" / "provider_patches" / "global_stream_presentation_v1.py"
spec = importlib.util.spec_from_file_location("global_stream_presentation_unknown_quality_test", presentation_path)
assert spec and spec.loader
presentation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(presentation)


def project(raw_quality: str, raw_resolution: str | None = None) -> dict:
    resolution = "" if raw_resolution is None else ",resolution:" + json.dumps(raw_resolution)
    source = (
        "module.exports={getStreams:async()=>[{name:'Kehflix',url:'https://media.example/master.m3u8',"
        + "quality:" + json.dumps(raw_quality) + resolution + "}]};\n"
    )
    patched = presentation.apply(source, context={"provider_id": "kehflix"})
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        provider = root / "provider.cjs"
        runner = root / "runner.cjs"
        provider.write_text(patched, encoding="utf-8")
        runner.write_text(
            "const p=require(" + json.dumps(str(provider)) + ");"
            "p.getStreams({mediaType:'movie',title:'Film',year:2026})"
            ".then(v=>console.log(JSON.stringify(v[0])));",
            encoding="utf-8",
        )
        result = subprocess.run(
            ["node", str(runner)],
            text=True,
            encoding="utf-8",
            errors="strict",
            capture_output=True,
            timeout=15,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout.strip())


for token in ("Unknown", "Inconnu", "Inconnue", "N/A"):
    row = project(token, token)
    assert row["title"] == "Kehflix", row
    assert row["name"] == "Kehflix", row
    assert "quality" not in row, row
    assert "resolution" not in row, row
    assert token.casefold() not in json.dumps(row, ensure_ascii=False).casefold(), row

known = project("1080p")
assert known["quality"] == "1080p", known
assert known["title"] == "Kehflix - 1080p", known

print("GLOBAL_STREAM_UNKNOWN_QUALITY_PROJECTION_OK unknown_fields=removed known_quality=preserved")
