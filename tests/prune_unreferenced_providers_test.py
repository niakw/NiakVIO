#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "prune_unreferenced_providers.py"
WORKFLOW = (REPO / ".github/workflows/sync.yml").read_text(encoding="utf-8")
assert WORKFLOW.count("git add -A providers") >= 2, "both publication phases must stage provider deletions"

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    providers = root / "providers"
    providers.mkdir()
    lkg = providers / "movix--nuvio--1111111111111111.js"
    published = providers / "movix--nuvio--2222222222222222.js"
    pending = providers / "movix--nuvio--3333333333333333.js"
    stale = providers / "movix--nuvio--4444444444444444.js"
    source = providers / "movix.js"
    for path in (lkg, published, pending, stale, source):
        path.write_text("module.exports = {};\n", encoding="utf-8")

    # During phase one, both the currently published manifest and the pending
    # manifest are authoritative. Publishing new bundles must never delete the
    # bundle still referenced by clients reading manifest.json.
    (root / "manifest.json").write_text(
        json.dumps({"scrapers": [{"url": "providers/movix--nuvio--2222222222222222.js"}]}),
        encoding="utf-8",
    )
    (root / "manifest.next.json").write_text(
        json.dumps({"scrapers": [{"url": "https://example.invalid/providers/movix--nuvio--3333333333333333.js?x=1"}]}),
        encoding="utf-8",
    )
    (root / "provider-lkg.json").write_text(
        json.dumps({"providers": {"movix": {"filename": "providers/movix--nuvio--1111111111111111.js"}}}),
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(SCRIPT), "--root", str(root)],
        text=True,
        capture_output=True,
        check=True,
    )
    assert lkg.exists(), result.stdout
    assert published.exists(), "phase one deleted the live published bundle"
    assert pending.exists(), "phase one deleted the pending bundle"
    assert source.exists(), result.stdout
    assert not stale.exists(), "unreferenced bundle was not pruned"
    assert "manifest.next.json,manifest.json" in result.stdout, result.stdout

    # Once the pending manifest is promoted, the old published bundle is no
    # longer live and may be removed. LKG/source inputs remain protected.
    (root / "manifest.json").write_text(
        json.dumps({"scrapers": [{"url": "providers/movix--nuvio--3333333333333333.js"}]}),
        encoding="utf-8",
    )
    (root / "manifest.next.json").unlink()
    result = subprocess.run(
        ["python3", str(SCRIPT), "--root", str(root)],
        text=True,
        capture_output=True,
        check=True,
    )
    assert lkg.exists(), result.stdout
    assert not published.exists(), "old bundle survived after manifest promotion"
    assert pending.exists(), result.stdout
    assert source.exists(), result.stdout

print("provider prune test passed")
