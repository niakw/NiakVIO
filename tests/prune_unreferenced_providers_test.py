#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "prune_unreferenced_providers.py"
WORKFLOW = (REPO / ".github/workflows/sync.yml").read_text(encoding="utf-8")

# ARCHI2 has one atomic publication transaction. Provider deletions must be
# staged in that transaction after the final prune, not in two competing
# publication phases.
assert WORKFLOW.count("git add -A providers") == 1, (
    "ARCHI2 must stage provider additions/deletions exactly once in its atomic publication transaction"
)
assert WORKFLOW.rfind("python scripts/prune_unreferenced_providers.py") < WORKFLOW.index("git add -A providers"), (
    "the final provider prune must complete before the atomic provider tree is staged"
)
assert "provider_catalog.json" in WORKFLOW, "provider pruning must publish with the canonical catalog transaction"

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

    # While a candidate manifest exists, both the currently published manifest
    # and the candidate transaction are authoritative. Pruning must never
    # delete the bundle still referenced by clients or the candidate awaiting
    # canonical-catalog import.
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
    assert published.exists(), "prune deleted the live published bundle before atomic promotion"
    assert pending.exists(), "prune deleted the pending candidate bundle before atomic promotion"
    assert source.exists(), result.stdout
    assert not stale.exists(), "unreferenced bundle was not pruned"
    assert "manifest.next.json,manifest.json" in result.stdout, result.stdout

    # Once the candidate has been imported/promoted, the former published
    # bundle is no longer live and may be removed. LKG/source inputs remain
    # protected.
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
    assert not published.exists(), "old bundle survived after candidate promotion"
    assert pending.exists(), result.stdout
    assert source.exists(), result.stdout

print("ARCHI2 atomic provider prune test passed")
