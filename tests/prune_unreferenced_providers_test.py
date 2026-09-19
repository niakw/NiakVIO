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


def generation(root: Path, number: int) -> Path:
    digest = f"{number:016x}"
    path = root / "providers" / f"movix--nuvio--{digest}.js"
    path.write_text(f"module.exports = {{ generation: {number} }};\n", encoding="utf-8")
    return path


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def write_current(root: Path, path: Path) -> None:
    rel = relative(path, root)
    (root / "manifest.json").write_text(
        json.dumps({"scrapers": [{"url": rel}]}),
        encoding="utf-8",
    )
    (root / "PROVENANCE.json").write_text(
        json.dumps({"providers": {"movix": {"published_filename": rel}}}),
        encoding="utf-8",
    )


def run_pruner(root: Path) -> None:
    subprocess.run(
        ["python3", str(SCRIPT), "--root", str(root), "--retention-generations", "10"],
        text=True,
        capture_output=True,
        check=True,
    )


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    providers = root / "providers"
    providers.mkdir()
    source = providers / "movix.js"
    source.write_text("module.exports = {};\n", encoding="utf-8")

    gens: dict[int, Path] = {}
    for number in range(1, 11):
        gens[number] = generation(root, number)
        write_current(root, gens[number])
        run_pruner(root)
        existing = sorted(providers.glob("movix--nuvio--*.js"))
        assert len(existing) == number, f"generation {number} must not prune inside the 10-generation window"

    # The 11th occurrence removes exactly the oldest generation, not every file
    # that happened to be unreferenced for ten maintenance runs.
    gens[11] = generation(root, 11)
    write_current(root, gens[11])
    run_pruner(root)
    assert not gens[1].exists(), "generation 11 must evict only generation 1"
    assert all(gens[n].exists() for n in range(2, 12))
    assert len(list(providers.glob("movix--nuvio--*.js"))) == 10

    # The rolling window advances one oldest occurrence at a time.
    gens[12] = generation(root, 12)
    write_current(root, gens[12])
    run_pruner(root)
    assert not gens[2].exists(), "generation 12 must evict generation 2"
    assert all(gens[n].exists() for n in range(3, 13))
    assert len(list(providers.glob("movix--nuvio--*.js"))) == 10

    # Re-referencing an older SHA is a fresh occurrence (rollback/LKG recovery),
    # so it moves to the newest end of the retention order.
    write_current(root, gens[5])
    run_pruner(root)
    gens[13] = generation(root, 13)
    write_current(root, gens[13])
    run_pruner(root)
    assert not gens[3].exists(), "rollback to generation 5 must not make generation 5 the next eviction"
    assert gens[5].exists()
    assert gens[4].exists()

    # LKG protection is absolute even when the protected SHA is the oldest.
    (root / "provider-lkg.json").write_text(
        json.dumps({"providers": {"movix": {"filename": relative(gens[4], root)}}}),
        encoding="utf-8",
    )
    gens[14] = generation(root, 14)
    write_current(root, gens[14])
    run_pruner(root)
    assert gens[4].exists(), "LKG generation must never be pruned"
    assert not gens[6].exists(), "the oldest unprotected generation must be evicted instead"

    # manifest.next.json receives the same transaction protection.
    (root / "manifest.next.json").write_text(
        json.dumps({"scrapers": [{"url": relative(gens[7], root)}]}),
        encoding="utf-8",
    )
    gens[15] = generation(root, 15)
    write_current(root, gens[15])
    run_pruner(root)
    assert gens[7].exists(), "pending manifest generation must be protected"
    assert not gens[8].exists(), "rolling eviction must skip protected pending/LKG generations"
    assert source.exists(), "plain provider source files are never pruned"

    ledger = json.loads((providers / ".generation-retention.json").read_text(encoding="utf-8"))
    assert ledger["schema_version"] == 2
    assert ledger["retention_generations"] == 10
    assert ledger["policy"] == "rolling-content-addressed-provider-generations"
    order = ledger["order"]["movix"]
    assert len(order) == 10
    assert relative(gens[5], root) in order
    assert relative(gens[4], root) in order
    assert relative(gens[15], root) in order

print("ARCHI2 rolling provider generation retention test passed")


# Security revocation overrides the rolling window but never authoritative state.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    providers = root / "providers"
    bases = root / "provider-bases"
    providers.mkdir()
    bases.mkdir()

    current = providers / "demo--nuvio--0000000000000002.js"
    current.write_text("module.exports={};\n", encoding="utf-8")
    old = providers / "demo--nuvio--0000000000000001.js"
    old.write_text("module.exports={};\n", encoding="utf-8")
    old_base = bases / "demo--base--0000000000000001.js"
    old_base.write_text("module.exports={};\n", encoding="utf-8")

    current_rel = relative(current, root)
    (root / "manifest.json").write_text(json.dumps({"scrapers":[{"url":current_rel}]}), encoding="utf-8")
    (root / "PROVENANCE.json").write_text(
        json.dumps({"providers":{"demo":{"published_filename":current_rel}}}),
        encoding="utf-8",
    )
    (root / "provider-security-revocations.json").write_text(
        json.dumps({"schema_version":1,"entries":[
            {"path":relative(old, root),"reason":"test"},
            {"path":relative(old_base, root),"reason":"test"},
        ]}),
        encoding="utf-8",
    )
    run_pruner(root)
    assert current.exists()
    assert not old.exists(), "unreferenced security-revoked provider must be removed immediately"
    assert not old_base.exists(), "unreferenced security-revoked ProviderBase must be removed immediately"

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    providers = root / "providers"
    providers.mkdir()
    current = providers / "demo--nuvio--0000000000000001.js"
    current.write_text("module.exports={};\n", encoding="utf-8")
    current_rel = relative(current, root)
    (root / "manifest.json").write_text(json.dumps({"scrapers":[{"url":current_rel}]}), encoding="utf-8")
    (root / "PROVENANCE.json").write_text(
        json.dumps({"providers":{"demo":{"published_filename":current_rel}}}),
        encoding="utf-8",
    )
    (root / "provider-security-revocations.json").write_text(
        json.dumps({"schema_version":1,"entries":[{"path":current_rel,"reason":"test"}]}),
        encoding="utf-8",
    )
    failed = subprocess.run(
        ["python3", str(SCRIPT), "--root", str(root), "--retention-generations", "10"],
        text=True, capture_output=True, check=False,
    )
    assert failed.returncode != 0
    assert "still authoritative" in (failed.stdout + failed.stderr)
    assert current.exists(), "protected revoked artifact must fail closed rather than disappear"
