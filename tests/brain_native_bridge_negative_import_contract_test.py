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
expected = next(x for x in source["experiments"] if x.get("id") == "tv-french-manga-44620517326-v27")
rows = [json.loads(line) for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines() if line.strip()]
all_negative = [row for row in rows if row.get("source") == "official-tv-executed-negative"]
matched = [row for row in all_negative
           if row.get("candidate_js_sha256") == expected["candidateJsSha256"]]
assert len(matched) == 1, matched
assert all(row.get("proof_authority") is False and row.get("prior_only") is True
           and row.get("result") == "rejected_executed_no_improvement"
           for row in all_negative)
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
# Verify the *next* leg of the actual pinned Brain pipeline, not only
# the presence of an imported JSONL record. Generic top-six RAG can otherwise
# bury a new executed negative behind many old provider histories.
sys.path.insert(0, str(root / "brain-llm" / "src"))
from niakvio_brain_llm.contracts import RepairRequest
from niakvio_brain_llm.planner import BrainPlanner
from niakvio_brain_llm.prompting import _bounded_force_hosted_negative_hints
from niakvio_brain_llm.retrieval import ExperienceStore

store = ExperienceStore.from_jsonl(sys.argv[1])
reserved = store.same_provider_executed_negatives(expected["provider"], limit=2)
assert any(
    item.get("experience_id") == row["experience_id"]
    and item.get("proof_authority") is False
    and item.get("prior_only") is True
    for item in reserved
), "source-pinned native negative was imported but not reserved for FORCE"
hints = _bounded_force_hosted_negative_hints(reserved, expected["provider"])
assert any(
    hint.get("mechanism") == "native_blocking_bridge_defeats_js_promise_hedge"
    and hint.get("do_not_repeat_js_only_hedge_without_nonblocking_host_bridge") is True
    and hint.get("provider_mutation_authority") is False
    and hint.get("proof_authority") is False
    for hint in hints
), "source-pinned native negative did not reach bounded FORCE prompt"
for hint in hints:
    wire_hint = json.dumps(hint, sort_keys=True)
    for secret in ("https://", "token=", "Cookie", "Authorization", "signedUrl"):
        assert secret not in wire_hint, secret
planner = BrainPlanner(backend=object(), store=store)
request = RepairRequest(
    provider_id=expected["provider"],
    failure_class="media_extraction_gap",
    status="REGRESSION PROVIDER",
    allowed_mutations=["provider_patch"],
)
prepared, _, _, _, _ = planner._prepare(request, compact_force=True)
assert any(
    item.get("experience_id") == row["experience_id"] for item in prepared
), "FORCE preparation lost the reserved executed negative"
assert store.same_provider_executed_negatives("unrelated-provider") == []
print(
    "FIELD_BRAIN_NEGATIVE_FORCE source_pinned=true "
    "imported=true reserved=true prompt=true planner=true "
    "rejected=true proof_authority=false"
)
print("FIELD_BRAIN_NEGATIVE_IMPORT source_pinned=true rejected=true provider_count=1 proof_authority=false")
