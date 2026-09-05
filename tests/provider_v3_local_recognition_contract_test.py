#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/provider-v3-reconstruct-all.yml"
ENTRY = ROOT / "scripts/enrich_provider_v3_static_knowledge.py"
LOCAL = ROOT / "scripts/provider_contract_local_enricher.py"
SEEDS = ROOT / "automation/provider-v3-recognition-seeds.json"
KNOWLEDGE = ROOT / "automation/provider-v3-static-knowledge.json"

workflow = WORKFLOW.read_text(encoding="utf-8")
entry = ENTRY.read_text(encoding="utf-8")
local = LOCAL.read_text(encoding="utf-8")
seeds = json.loads(SEEDS.read_text(encoding="utf-8"))
knowledge = json.loads(KNOWLEDGE.read_text(encoding="utf-8"))

# Ordinary 96/96 reconstruction must be self-contained after NiakVIO has learned
# a provider contract. External repositories are research inputs only.
for forbidden in (
    "python scripts/discover_candidates.py",
    "python scripts/finalize_gowaru_provider_v3_source_plans.py",
    "refresh_static_knowledge",
    "raw.githubusercontent.com/Gowaru/",
    "raw.githubusercontent.com/yoruix/",
    "raw.githubusercontent.com/NuvioPlugin/",
):
    assert forbidden not in workflow, f"ordinary reconstruction regained external dependency: {forbidden}"

assert "provider_contract_local_enricher" in entry
assert "provider_contract_recognizer" not in entry

# Reject actual network client imports/usages, not harmless local variables named
# `requests` that hold normalized request-contract DATA.
for pattern in (
    r"^\s*(?:from\s+urllib|import\s+urllib)(?:\.|\s)",
    r"^\s*(?:from\s+requests|import\s+requests)(?:\.|\s|$)",
    r"^\s*(?:from\s+httpx|import\s+httpx)(?:\.|\s|$)",
    r"^\s*(?:from\s+socket|import\s+socket)(?:\.|\s|$)",
    r"\burllib\.request\.",
    r"\brequests\.(?:get|post|put|patch|delete|request|Session)\b",
    r"\bhttpx\.(?:get|post|put|patch|delete|request|Client|AsyncClient)\b",
):
    assert not re.search(pattern, local, re.M), f"local recognition regained network capability: {pattern}"
assert "raw.githubusercontent.com" not in local
assert "externalRepositories=0" in local

assert seeds.get("schemaVersion") == 1
assert seeds.get("role") == "niakvio-owned-recognition-seeds"
assert seeds.get("externalRepositoryRequired") is False
assert seeds.get("providerJavaScriptExecuted") is False
seed_providers = seeds.get("providers")
assert isinstance(seed_providers, dict)
for provider_id in ("animekai", "animezey", "anime-ultime"):
    assert provider_id in seed_providers, provider_id
    row = seed_providers[provider_id]
    assert isinstance(row.get("routes"), list) and row["routes"], provider_id

providers = knowledge.get("providers")
assert isinstance(providers, dict) and len(providers) == 96
assert knowledge.get("legacyProviderJsExecuted") is False
assert knowledge.get("upstreamJsExecuted") is False

print(
    "Provider v3 local recognition contract passed "
    f"providers={len(providers)} seeds={len(seed_providers)} externalRepositories=0"
)
