#!/usr/bin/env python3
"""Fail closed on a stale Brain-LLM gitlink or unaudited source pairing."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN = ROOT / "automation/brain-pinned-source.json"
raw = json.loads(PIN.read_text(encoding="utf-8"))
assert raw.get("schemaVersion") == 1
assert raw.get("role") == "validated-external-brain-gitlink"
assert raw.get("repository") == "niakw/NiakVIO-Brain-LLM"
assert raw.get("submodule") == "brain-llm"
sha = str(raw.get("sha") or "")
assert re.fullmatch(r"[a-f0-9]{40}", sha)
assert raw.get("brainCiConclusion") == "success"
assert raw.get("brainSecurityConclusion") == "success"
assert re.fullmatch(r"[0-9]{8,14}", str(raw.get("brainCiRunId") or ""))
assert re.fullmatch(r"[0-9]{8,14}", str(raw.get("brainSecurityRunId") or ""))
assert raw.get("providerRepairCount") == 0
assert raw.get("proofAuthority") is False
assert raw.get("publicationAuthority") is False
entry = subprocess.check_output(
    ["git", "ls-tree", "HEAD", "--", "brain-llm"],
    cwd=ROOT, text=True
).strip()
match = re.fullmatch(r"160000 commit ([a-f0-9]{40})\tbrain-llm", entry)
assert match, f"expected git submodule, got {entry!r}"
assert match.group(1) == sha, (
    "Brain source pin drift: expected exact validated Brain SHA "
    f"{sha}, checked-in gitlink {match.group(1)}"
)
gitmodules = (ROOT / ".gitmodules").read_text(encoding="utf-8")
assert "https://github.com/niakw/NiakVIO-Brain-LLM.git" in gitmodules
print(f"FIELD_BRAIN_SUBMODULE_EXACT_PIN verified=true source_sha={sha} repair_count=0")

# Operational triggers may describe intent, but version provenance has one
# authority only: the validated gitlink pin above. Historical SHAs in the
# trigger become stale silently and must never return as a competing truth.
trigger = (ROOT / ".github/triggers/brain-learning-reconstruction").read_text(
    encoding="utf-8"
)
for forbidden in (
    "source_brain_main_sha:",
    "source_niakvio_main_pretrigger_sha:",
):
    assert forbidden not in trigger, (
        f"operational Brain trigger reintroduced duplicated provenance: {forbidden}"
    )
assert "causal_frontier:" in trigger
assert "architecture_force:" in trigger
assert "target_provider:" in trigger

# The active source->Brain integration gate must select the latest exact-parent
# evidence by provenance. It must not freeze a historical probe count or run ID,
# otherwise new valid observations are rejected while old evidence keeps winning.
integration = (ROOT / "scripts/assert_brain_catalogue_integration.py").read_text(
    encoding="utf-8"
)
assert "assert len(probes) ==" not in integration
assert not re.search(r'probeRunId[^\n]{0,80}["\']?[0-9]{8,20}', integration), (
    "active source-memory gate must not pin one historical probe run"
)
assert "exact_parent_match" in integration
assert "current = max(matched, key=run_number)" in integration

print("FIELD_BRAIN_SINGLE_AUTHORITY_CONTRACT verified=true")
