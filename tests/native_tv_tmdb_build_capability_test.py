#!/usr/bin/env python3
"""Title-first native TV corpus must not mistake a keyless build for provider failure."""
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/prepare_native_tv_tmdb_contract.py"
spec = importlib.util.spec_from_file_location("tv_tmdb", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as folder:
    root = Path(folder) / "niakvio"
    client = Path(folder) / "nuvio-tv"
    (root / "providers").mkdir(parents=True)
    (root / "vf").mkdir()
    client.mkdir()
    (client / "local.properties").write_text("sdk.dir=/opt/android-sdk\n")
    (root / "providers/title-first.js").write_text(
        'const CONFIG = {"identityInput":{"requiresTmdbBeforeRun":true}};\n')
    (root / "providers/no-metadata.js").write_text('var x = 1;\n')
    (root / "manifest.json").write_text(json.dumps({"scrapers": [
        {"id": "TITLE-FIRST", "enabled": True, "filename": "providers/title-first.js"},
        {"id": "NO-METADATA", "enabled": True, "filename": "providers/no-metadata.js"},
    ]}))
    (root / "vf/manifest.json").write_text(json.dumps({"scrapers": [
        {"id": "TITLE-FIRST", "enabled": True, "filename": "../providers/title-first.js"}
    ]}))
    assert mod.source_requires_tmdb(root, "manifest.json", "title-first")
    assert mod.source_requires_tmdb(root, "vf/manifest.json", "title-first")
    assert not mod.source_requires_tmdb(root, "manifest.json", "no-metadata")
    assert not mod.source_requires_tmdb(root, "manifest.json", "declared-type")
    try:
        mod.inject(root, client, "manifest.json", "title-first", "")
    except ValueError as error:
        assert "TMDB_REQUIRED_BUT_UNAVAILABLE" in str(error)
    else:
        raise AssertionError("empty key let title-first provider produce false 0-stream evidence")
    assert "TMDB_API_KEY" not in (client / "local.properties").read_text()
    key = "abcdef0123456789abcdef0123456789"
    with redirect_stdout(io.StringIO()) as output:
        assert mod.inject(root, client, "vf/manifest.json", "title-first", key) == "configured"
    assert key not in output.getvalue()
    assert (client / "local.properties").read_text().count("TMDB_API_KEY=") == 1
    assert "sdk.dir=/opt/android-sdk" in (client / "local.properties").read_text()
    assert mod.inject(root, client, "manifest.json", "title-first", key) == "configured"
    assert (client / "local.properties").read_text().count("TMDB_API_KEY=") == 1
    assert mod.inject(root, client, "manifest.json", "no-metadata", "") == "not_required_and_unconfigured"
    for bad in ("abc", "token\ninjection", "C" * 33):
        try:
            mod.inject(root, client, "manifest.json", "title-first", bad)
        except ValueError:
            pass
        else:
            raise AssertionError("rejected malformed TMDB key")
    invalid = {"scrapers": [{
        "id": "TITLE-FIRST", "enabled": True, "filename": "../other/exfiltrate.js"
    }]}
    (root / "manifest.json").write_text(json.dumps(invalid))
    try:
        mod.source_requires_tmdb(root, "manifest.json", "title-first")
    except ValueError:
        pass
    else:
        raise AssertionError("escaped provider path accepted")

workflow = (ROOT / ".github/workflows/native-corpus-device-targeted.yml").read_text()
assert "prepare_native_tv_tmdb_contract.py" in workflow
assert "TMDB_API_KEY: ${{ secrets.TMDB_API_KEY }}" in workflow
assert "touch nuvio-tv/local.properties" in workflow
assert "FIELD_NATIVE_TV_TMDB_CAPABILITY" in SCRIPT.read_text()
assert "get_tmdb" not in workflow.lower() or "TMDB_API_KEY" in workflow
print("Native TV TMDB build capability keyless-fail-closed test passed")
