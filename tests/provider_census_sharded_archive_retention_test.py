#!/usr/bin/env python3
"""Assert Git-backed census pruning retained exact evidence references."""
from pathlib import Path
import json
import re
root=Path(__file__).resolve().parents[1]
x=json.loads((root/"automation/provider-census-sharded-archive-index.json").read_text())
assert x["schemaVersion"]==1 and x["kind"]=="git-history-backed-pruned-census-snapshots"
assert re.fullmatch(r"[a-f0-9]{40}",x["sourceCommitSha"])
assert re.fullmatch(r"[a-f0-9]{40}",x["sourceTreeSha"])
entries=x["entries"]
kept=x["retainedPaths"]
assert len(entries)==x["archivedFromMain"]>=1000
assert len(kept)==x["retainedOnMain"]>=64
assert x["countBefore"]==len(kept)+len(entries)
assert sum(e["size"] for e in entries)==x["archivedBytes"]
pattern=re.compile(r"automation/provider-census-sharded-[0-9]{8,20}\\.json")
assert len(set(kept))==len(kept)
assert len({e["path"] for e in entries})==len(entries)
assert set(kept).isdisjoint(e["path"] for e in entries)
for row in entries:
    assert pattern.fullmatch(row["path"]),row
    assert re.fullmatch(r"[a-f0-9]{40}",row["blobSha"]),row
    assert row["size"]>0
    assert not (root/row["path"]).exists(),row
for p in kept:
    assert pattern.fullmatch(p),p
    assert (root/p).is_file(),p
assert (root/"automation/provider-census-sharded-latest.json").is_file()
assert (root/"automation/provider-census-sharded-latest-summary.json").is_file()
print(json.dumps({"archive":"git-history-retained","pruned":len(entries),"bytes":x["archivedBytes"],"retained":len(kept),"playback_proof":False},sort_keys=True))
