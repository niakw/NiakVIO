#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/classify_provider_authority.py"
spec=importlib.util.spec_from_file_location("authority",SCRIPT)
assert spec and spec.loader
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def row(enabled=True):
    return {"id":"demo","enabled":enabled}

def reg(**kw):
    base={"sources":[],"search_queries":[],"direct":None}
    base.update(kw)
    return base

def patch(**kw):
    base={"capability":"html_scraper","manifest_overrides":{"enabled":True}}
    base.update(kw)
    return base

# Search is supplementary: a site-dependent provider with only search is not
# allowed to burn Repair cycles before address authority is established.
r=module.classify("demo",row(),reg(search_queries=["demo official"],legacy_search_refresh=True),patch(),{})
assert r["action"]=="REDISCOVER_SEARCH",r
assert r["repairEligible"] is False

# Two persisted Domain failures convert unresolved site identity to a safe off
# decision; one transient failure does not.
r=module.classify("demo",row(),reg(search_queries=["demo"]),patch(),{"authority_failures":{"consecutive":1}})
assert r["action"]=="REDISCOVER_SEARCH",r
r=module.classify("demo",row(),reg(search_queries=["demo"]),patch(),{"authority_failures":{"consecutive":2}})
assert r["action"]=="DISABLE_AUTHORITY_EXHAUSTED",r

# API/backends are independent from a homepage/hub when structured authority is
# explicit. This is the PersianStremio/YFlix class.
r=module.classify(
    "demo",row(),reg(search_queries=["demo"]),
    patch(capability="api_stream_resolver",official_api="https://api.example.test",
          learned_routes=["/stream/movie/{id}.json"]),
    {"authority_failures":{"consecutive":9}},
)
assert r["action"]=="KEEP_BACKEND",r
assert r["repairEligible"] is True

# A removed authoritative directory source is stronger negative evidence than
# search noise for a site-dependent provider.
r=module.classify(
    "demo",row(),
    reg(sources=[{"type":"hub","url":"https://directory.example/demo","source_status":"removed"}]),
    patch(),
    {},
)
assert r["action"]=="DISABLE_SOURCE_REMOVED",r

# Explicit-current direct is usable while fresh observations do not contradict
# it, but repeated failures first force rediscovery and then safe disable.
direct=reg(direct="https://demo.example/",direct_authority="explicit_current")
r=module.classify("demo",row(),direct,patch(),{"authority_failures":{"consecutive":0}})
assert r["action"]=="KEEP_DIRECT",r
r=module.classify("demo",row(),direct,patch(),{"authority_failures":{"consecutive":2}})
assert r["action"]=="REDISCOVER_DIRECT",r
r=module.classify("demo",row(),direct,patch(),{"authority_failures":{"consecutive":3}})
assert r["action"]=="DISABLE_AUTHORITY_EXHAUSTED",r

# A non-explicit curated direct needs provider-owned route proof. The URL alone
# is a rediscovery candidate, not authority.
r=module.classify("demo",row(),reg(direct="https://demo.example/"),patch(),{})
assert r["action"]=="REDISCOVER_DIRECT",r
proven_direct_patch=patch(
    route_proof={
        "provenRouteCount": 1,
        "lastRepairProbe": {"positiveExecutionEvidence": True},
    }
)
r=module.classify("demo",row(),reg(direct="https://demo.example/"),proven_direct_patch,{})
assert r["action"]=="KEEP_DIRECT",r
assert r["repairEligible"] is True,r

# A mixed embed resolver may be driven by an explicit delegated DB/API backend.
r=module.classify(
    "demo",row(),reg(search_queries=["demo"]),
    patch(capability="mixed_embed_resolver",provider_lego_options={"runtime":{"db":"https://backend.example/db","api":"https://backend.example/api"}}),
    {},
)
assert r["action"]=="KEEP_BACKEND",r

# Shared identity infrastructure must not establish provider backend authority.
# The provider may still be Repair-eligible through its own site + route proof.
r=module.classify(
    "demo",row(),reg(search_queries=["demo"]),
    patch(
        capability="mixed_embed_resolver",
        official_site="https://demo.example",
        api_recipe={"base":"https://arm.haglund.dev"},
        route_proof={"provenRouteCount":2,"lastRepairProbe":{"positiveExecutionEvidence":True}},
    ),
    {},
)
assert r["action"]=="KEEP_PROVEN_SITE",r
assert "backendUrls" not in r

# fallbackBases are site failovers, not deterministic backend authority.
r=module.classify(
    "demo",row(),reg(search_queries=["demo"]),
    patch(
        official_site="https://demo.example",
        provider_lego_options={"runtime":{"fallbackBases":["https://mirror.example"]}},
        route_proof={"provenRouteCount":1,"lastRepairProbe":{"positiveExecutionEvidence":True}},
    ),
    {},
)
assert r["action"]=="KEEP_PROVEN_SITE",r

# Structured site + positive route proof is a valid medium-confidence historical combo.
r=module.classify(
    "demo",row(),reg(search_queries=["demo"]),
    patch(official_site="https://demo.example",route_proof={"provenRouteCount":2,"lastRepairProbe":{"positiveExecutionEvidence":True}}),
    {},
)
assert r["action"]=="KEEP_PROVEN_SITE",r

# Fresh historical combinations may unlock Repair without promoting search itself.
from datetime import datetime, timezone
fresh={"current":{"url":"https://demo.example","last_seen":datetime.now(timezone.utc).isoformat()}}
r=module.classify(
    "demo",row(),
    reg(search_queries=["demo"],legacy_search_refresh=True,direct_candidates=["https://demo.example"]),
    patch(),fresh,
)
assert r["action"]=="KEEP_LIVE_CANDIDATE",r
r=module.classify(
    "demo",row(),
    reg(search_queries=["demo"],legacy_search_refresh=True),
    patch(route_proof={"provenRouteCount":1,"lastRepairProbe":{"positiveExecutionEvidence":True}}),fresh,
)
assert r["action"]=="KEEP_LKG_COMBO",r

# A bare direct candidate sourced only from search is not authority by itself.
bare_direct = reg(direct="https://candidate.example/")
bare_direct["sources"] = [{"type":"search","query":"demo official"}]
r = module.classify("demo", row(True), bare_direct, patch(), {})
assert r["action"] == "REDISCOVER_SEARCH", r
assert r["repairEligible"] is False, r

# The same non-explicit direct becomes usable once provider-owned execution has
# produced positive route evidence.
proven = patch()
proven["route_proof"] = {
    "provenRouteCount": 1,
    "lastRepairProbe": {"positiveExecutionEvidence": True},
}
r = module.classify("demo", row(True), bare_direct, proven, {})
assert r["action"] == "KEEP_DIRECT", r
assert r["repairEligible"] is True, r

# explicit_current remains an intentional stronger authority until persisted
# Domain failure memory demotes it.
explicit = reg(direct="https://current.example/")
explicit["direct_authority"] = "explicit_current"
r = module.classify("demo", row(True), explicit, patch(), {})
assert r["action"] == "KEEP_DIRECT", r
assert r["confidence"] == "high", r

# A newly curated manual-off decision on an enabled provider must enter the
# standard disabled-retention lifecycle immediately instead of remaining merely
# Repair-blocked while still executable.
manual_registry=reg(manual_off_reason="manual_off_no_current_authority_search_only")
r=module.classify("demo",row(True),manual_registry,patch(),{})
assert r["action"]=="DISABLE_MANUAL_POLICY",r
assert r["repairEligible"] is False,r
manifest_row=row(True)
manual_patch=patch()
reason=module.apply_disable(manifest_row,manual_registry,manual_patch,r["action"])
assert reason=="manual_off_no_current_authority_search_only",reason
assert manifest_row["enabled"] is False,manifest_row
assert manifest_row["disabledReason"]==reason,manifest_row
assert manual_patch["manifest_overrides"]["enabled"] is False,manual_patch
assert manual_patch["route_data_state"]=="off",manual_patch
assert manual_registry["manifest_status"]=="Désactivé",manual_registry
assert manual_registry["activation_eligible"] is False,manual_registry

# Existing manual lifecycle decisions remain terminal.
r=module.classify("demo",row(False),reg(),patch(manual_off_reason="manual_off_test"),{})
assert r["action"]=="KEEP_DISABLED",r

assert "PROVIDER_AUTHORITY_BACKEND_SCOPE_V1" in SCRIPT.read_text(encoding="utf-8")
assert "PROVIDER_AUTHORITY_DIRECT_PROOF_V1" in SCRIPT.read_text(encoding="utf-8")
assert module.ROOT.joinpath("scripts/manage_provider_lifecycle.py").read_text(encoding="utf-8").find("RETENTION_DAYS = 7")>=0
print("provider authority arbiter contract ok")
