#!/usr/bin/env python3
"""Proof that the pinned Brain actually imports the executed native negative."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

assert len(sys.argv) == 2, "expected JSONL export from pinned Brain importer"
root = Path(__file__).resolve().parents[1]
source = json.loads((root / "automation/native-bridge-negative-experiments.json").read_text(encoding="utf-8"))
assert source.get("role") == "brain-native-bridge-negative-experiments"
assert source.get("schemaVersion") == 1
assert len(source.get("experiments") or []) >= 1
expected = source["experiments"][0]
rows = [json.loads(line) for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines() if line.strip()]
matched = [row for row in rows if row.get("source") == "official-tv-executed-negative"]
assert len(matched) == 1, matched
row = matched[0]
assert row.get("providers") == [expected["provider"]]
assert row.get("failure_class") == "synchronous_native_fetch_no_parallelism"
assert row.get("source_niakvio_sha") == expected["sourceNiakvioSha"]
assert row.get("official_client_sha") == expected["officialClientSha"]
assert row.get("candidate_js_sha256") == expected["candidateJsSha256"]
assert row.get("result") == "rejected_executed_no_improvement"
assert row.get("prior_only") is True
assert row.get("proof_authority") is False
assert "repeat_promise_all_hedge_without_async_host_capability" in row.get("avoid", [])
assert re.fullmatch(r"native-bridge-negative:[0-9]{8,14}:[a-f0-9]{16}", str(row.get("experience_id") or ""))
wire = json.dumps(row, sort_keys=True)
for secret in ("https://", "token=", "Cookie", "Authorization", "signedUrl"):
    assert secret not in wire, secret
print("FIELD_BRAIN_NEGATIVE_IMPORT source_pinned=true rejected=true provider_count=1 proof_authority=false")
