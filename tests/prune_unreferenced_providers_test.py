#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "prune_unreferenced_providers.py"
WORKFLOW = (REPO / ".github/workflows/sync.yml").read_text(encoding="utf-8")

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
    historical = providers / "movix--nuvio--5555555555555555.js"
    source = providers / "movix.js"
    for path in (lkg, published, pending, stale, historical, source):
        path.write_text("module.exports = {};\n", encoding="utf-8")

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
    (root / "PROVENANCE.json").write_text(
        json.dumps({"providers": {"movix": {
            "published_filename": "providers/movix--nuvio--2222222222222222.js",
            "canonical_source_filename": "providers/movix--nuvio--5555555555555555.js"
        }}}),
        encoding="utf-8",
    )

    # First publication cycle: unreferenced hashed generations are deliberately
    # retained for clients that may still hold an older manifest.
    result = subprocess.run(
        ["python3", str(SCRIPT), "--root", str(root), "--retention-cycles", "10"],
        text=True,
        capture_output=True,
        check=True,
    )
    assert lkg.exists(), result.stdout
    assert published.exists(), result.stdout
    assert pending.exists(), result.stdout
    assert stale.exists(), "first stale cycle must not delete an old client generation"
    assert historical.exists(), "historical hashed generation must receive the same grace"
    assert source.exists(), result.stdout
    ledger = json.loads((providers / ".generation-retention.json").read_text(encoding="utf-8"))
    assert ledger["stale_cycles"]["providers/movix--nuvio--4444444444444444.js"] == 1
    assert ledger["stale_cycles"]["providers/movix--nuvio--5555555555555555.js"] == 1

    # Active transaction finishes. Former published/pending bundles become stale,
    # but must also receive the complete grace period.
    (root / "manifest.json").write_text(
        json.dumps({"scrapers": [{"url": "providers/movix--nuvio--3333333333333333.js"}]}),
        encoding="utf-8",
    )
    (root / "manifest.next.json").unlink()
    (root / "PROVENANCE.json").write_text(
        json.dumps({"providers": {"movix": {
            "published_filename": "providers/movix--nuvio--3333333333333333.js"
        }}}),
        encoding="utf-8",
    )

    for cycle in range(2, 10):
        result = subprocess.run(
            ["python3", str(SCRIPT), "--root", str(root), "--retention-cycles", "10"],
            text=True,
            capture_output=True,
            check=True,
        )
        assert stale.exists(), f"stale bundle deleted too early at cycle {cycle}: {result.stdout}"
        assert historical.exists(), f"historical bundle deleted too early at cycle {cycle}: {result.stdout}"

    # A stale generation that becomes referenced again resets its age to zero.
    (root / "provider-lkg.json").write_text(
        json.dumps({"providers": {
            "movix": {"filename": "providers/movix--nuvio--1111111111111111.js"},
            "old-client": {"filename": "providers/movix--nuvio--5555555555555555.js"},
        }}),
        encoding="utf-8",
    )
    subprocess.run(
        ["python3", str(SCRIPT), "--root", str(root), "--retention-cycles", "10"],
        text=True,
        capture_output=True,
        check=True,
    )
    ledger = json.loads((providers / ".generation-retention.json").read_text(encoding="utf-8"))
    assert ledger["stale_cycles"]["providers/movix--nuvio--5555555555555555.js"] == 0
    assert historical.exists()

    # Remove that renewed reference. The other stale file reaches cycle 10 and
    # may now be removed; the reset generation begins a fresh grace period.
    (root / "provider-lkg.json").write_text(
        json.dumps({"providers": {"movix": {"filename": "providers/movix--nuvio--1111111111111111.js"}}}),
        encoding="utf-8",
    )
    result = subprocess.run(
        ["python3", str(SCRIPT), "--root", str(root), "--retention-cycles", "10"],
        text=True,
        capture_output=True,
        check=True,
    )
    assert not stale.exists(), "bundle must age out only after ten consecutive stale publication cycles"
    assert historical.exists(), "re-referenced generation must get a fresh ten-cycle grace"
    assert published.exists(), "former published generation has not yet accumulated ten stale cycles"
    assert pending.exists(), result.stdout
    assert source.exists(), "plain provider source files are never pruned"

print("ARCHI2 cyclic provider generation retention test passed")
