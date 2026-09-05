#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/provider-v3-reconstruct-all.yml"
ENTRY = ROOT / "scripts/enrich_provider_v3_static_knowledge.py"
LOCAL = ROOT / "scripts/provider_contract_local_enricher.py"
ROUTES = ROOT / "scripts/provider_route_reconstructor.py"
SEEDS = ROOT / "automation/provider-v3-recognition-seeds.json"
KNOWLEDGE = ROOT / "automation/provider-v3-static-knowledge.json"

workflow = WORKFLOW.read_text(encoding="utf-8")
entry = ENTRY.read_text(encoding="utf-8")
local = LOCAL.read_text(encoding="utf-8")
route_reconstructor = ROUTES.read_text(encoding="utf-8")
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
assert "reconstruct_provider_routes" in local
assert '"canonicalRouteData": "providers.<id>.model.routeData"' in local
assert "fullProviderReconstructionRequired" in route_reconstructor
assert "reconstruct_all_routes" in route_reconstructor

# Reject actual network client imports/usages from both production local recognition
# and the route-only reconstructor. They may statically inspect source text, never
# download or execute provider code.
for source_name, source in (("local", local), ("routes", route_reconstructor)):
    for pattern in (
        r"^\s*(?:from\s+urllib|import\s+urllib)(?:\.|\s)",
        r"^\s*(?:from\s+requests|import\s+requests)(?:\.|\s|$)",
        r"^\s*(?:from\s+httpx|import\s+httpx)(?:\.|\s|$)",
        r"^\s*(?:from\s+socket|import\s+socket)(?:\.|\s|$)",
        r"\burllib\.request\.",
        r"\brequests\.(?:get|post|put|patch|delete|request|Session)\b",
        r"\bhttpx\.(?:get|post|put|patch|delete|request|Client|AsyncClient)\b",
    ):
        assert not re.search(pattern, source, re.M), f"{source_name} recognition regained network capability: {pattern}"
    assert "raw.githubusercontent.com" not in source

assert "externalRepositories=0" in local
assert 'model["routeData"]' in route_reconstructor
assert 'model["routes"] = canonical_routes' in route_reconstructor
assert '"status": "recognized" if model["routeData"] else "unknown"' in route_reconstructor

# Functional route-object tests are part of the normal strategy gate through this
# child contract test, not an optional standalone check.
route_test = subprocess.run(
    [sys.executable, str(ROOT / "tests/provider_route_reconstructor_test.py")],
    cwd=ROOT,
    text=True,
    capture_output=True,
    check=False,
)
assert route_test.returncode == 0, route_test.stdout + route_test.stderr

assert seeds.get("schemaVersion") == 1
assert seeds.get("role") == "niakvio-owned-recognition-seeds"
assert seeds.get("externalRepositoryRequired") is False
assert seeds.get("providerJavaScriptExecuted") is False
seed_providers = seeds.get("providers")
assert isinstance(seed_providers, dict)
for provider_id in ("animekai", "animezey", "anime-ultime", "uhdmovies"):
    assert provider_id in seed_providers, provider_id
    row = seed_providers[provider_id]
    assert isinstance(row.get("routes"), list) and row["routes"], provider_id

uhd = seed_providers["uhdmovies"]
assert uhd["routes"] == ["/?s={query}"], uhd
assert "/movie/" not in uhd["routes"], uhd
assert any(
    request.get("route") == "/?s={query}"
    and request.get("role") == "search"
    and request.get("method") == "GET"
    and request.get("executedEvidence") is True
    for request in uhd.get("requests") or []
), uhd

providers = knowledge.get("providers")
assert isinstance(providers, dict) and len(providers) == 96
assert knowledge.get("legacyProviderJsExecuted") is False
assert knowledge.get("upstreamJsExecuted") is False

print(
    "Provider v3 local recognition contract passed "
    f"providers={len(providers)} seeds={len(seed_providers)} externalRepositories=0 routeData=model.routeData"
)
