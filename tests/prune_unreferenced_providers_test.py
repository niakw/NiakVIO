#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "prune_unreferenced_providers.py"

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    providers = root / "providers"
    providers.mkdir()
    keep = providers / "movix--nuvio--1111111111111111.js"
    stale = providers / "movix--nuvio--2222222222222222.js"
    source = providers / "movix.js"
    for path in (keep, stale, source):
        path.write_text("module.exports = {};\n", encoding="utf-8")

    (root / "manifest.json").write_text(
        json.dumps({"scrapers": [{"url": "providers/movix--nuvio--2222222222222222.js"}]}),
        encoding="utf-8",
    )
    (root / "manifest.next.json").write_text(
        json.dumps({"scrapers": [{"url": "https://example.invalid/providers/movix--nuvio--1111111111111111.js?x=1"}]}),
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(SCRIPT), "--root", str(root)],
        text=True,
        capture_output=True,
        check=True,
    )
    assert keep.exists(), result.stdout
    assert not stale.exists(), result.stdout
    assert source.exists(), result.stdout
    assert "removed=1" in result.stdout, result.stdout

print("provider prune test passed")
