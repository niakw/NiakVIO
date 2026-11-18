#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str((ROOT/"scripts").resolve()))
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
    base={"capability":"html_scraper","manifest_overrides":{}}
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

# An effective, official operator shutdown outranks stale backend authority.
# This prevents the Brain from "repairing" a retired service into a different
# upstream just because old API/backend metadata remains structured.
shutdown_registry = reg(
    lifecycle={
        "state": "upstream_shutdown",
        "effective_date": "2000-01-01",
        "source_type": "operator_notice",
        "source_url": "https://operator.example/shutdown",
    }
)
r=module.classify(
    "demo", row(), shutdown_registry,
    patch(
        capability="api_stream_resolver",
        official_api="https://api.example.test",
        learned_routes=["/stream/movie/{id}.json"],
    ),
    {},
)
assert r["action"]=="DISABLE_UPSTREAM_SHUTDOWN",r
assert r["repairEligible"] is False,r
assert r["authorityClass"]=="upstream-shutdown",r

future_shutdown = reg(
    lifecycle={
        "state": "upstream_shutdown",
        "effective_date": "2999-01-01",
        "source_type": "operator_notice",
        "source_url": "https://operator.example/shutdown",
    }
)
r=module.classify(
    "demo", row(), future_shutdown,
    patch(
        capability="api_stream_resolver",
        official_api="https://api.example.test",
        learned_routes=["/stream/movie/{id}.json"],
    ),
    {},
)
assert r["action"]=="KEEP_BACKEND",r

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

# Current canonical production bytes must have terminal playback proof. The
# exhaustive status matrix below owns this contract; retain one focused
# regression check here so the historical test section no longer encodes the
# obsolete REGRESSION-only policy.
regression = {
    "provider":"demo","status":"REGRESSION PROVIDER","testedThisRun":True,
    "brainCheckRequired":True,"repairEligible":True,
}
assert module.current_architecture_nonfunctional(regression) is True
assert module.current_architecture_nonfunctional({**regression,"testedThisRun":False}) is False
proof_refresh = {
    "provider":"demo","status":"PROOF REFRESH REQUIRED","testedThisRun":True,
    "brainCheckRequired":False,"repairEligible":False,
}
assert module.current_architecture_nonfunctional(proof_refresh) is False

# Missing current-byte positive proof is a freshness/validation debt, not
# evidence that the provider stopped functioning. This guards against mass
# disablement immediately after a shared Core/ProviderBase byte rotation.
for original in (
    {"action": "KEEP_BACKEND", "repairEligible": True, "reasons": ["backend"]},
    {"action": "REDISCOVER_SEARCH", "repairEligible": False, "reasons": ["search"]},
    {"action": "DISABLE_UPSTREAM_SHUTDOWN", "repairEligible": False, "reasons": ["operator_notice"]},
):
    original_reasons = list(original["reasons"])
    annotated = module.with_current_byte_proof_debt(
        original, proof_authority="no-current-byte-production-proof", current_status="NO PROOF"
    )
    assert annotated["action"] == original["action"], annotated
    assert annotated["repairEligible"] == original["repairEligible"], annotated
    assert annotated["productionFreshnessAuthorized"] is False, annotated
    assert annotated["productionProofAuthority"] == "no-current-byte-production-proof", annotated
    assert "current_bytes_lack_production_freshness_authority" in annotated["reasons"], annotated
    assert original["reasons"] == original_reasons, original
    assert annotated["reasons"][:len(original_reasons)] == original_reasons, annotated

# The owner must never replace a diagnosis with a synthetic nonfunctional
# verdict just because the current exact-byte proof is absent.
classifier_source = SCRIPT.read_text(encoding="utf-8")
main_classification = classifier_source.split(
    'if manifest_row.get("enabled") is not False and not production_authorized:', 1
)[1].split('if args.apply_safe_disables and result["action"] in {', 1)[0]
assert "with_current_byte_proof_debt(" in main_classification
assert '"action": "DISABLE_ARCHITECTURE_NONFUNCTIONAL"' not in main_classification
assert '"currentByteUnprovenEntersDisabledRetention": False' in classifier_source

# Deprecated proof-absence auto-off is rolled back to the underlying authority
# classification instead of remaining terminal lifecycle state. Stronger disable
# reasons are still evaluated after this rollback.
legacy_row={
    "id":"demo","enabled":False,
    "disabledReason":"auto_off_current_architecture_nonfunctional",
    "disabledAt":"2026-11-17","purgeAfter":"2026-11-24","lifecycleState":"disabled-retained",
}
legacy_registry=reg(manifest_status="Désactivé",activation_eligible=False,direct="https://demo.example/")
legacy_patch=patch(manifest_overrides={"enabled":False},route_data_state="off",activation_eligible=False,
                   route_proof={"provenRouteCount":1,"lastRepairProbe":{"positiveExecutionEvidence":True}})
assert module.restore_deprecated_nonfunctional_auto_off(legacy_row,legacy_registry,legacy_patch) is True
assert legacy_row["enabled"] is True and "disabledReason" not in legacy_row, legacy_row
assert legacy_patch["manifest_overrides"].get("enabled") is None, legacy_patch
assert "route_data_state" not in legacy_patch and "activation_eligible" not in legacy_patch, legacy_patch
assert legacy_registry["manifest_status"]=="Active" and "activation_eligible" not in legacy_registry, legacy_registry
r=module.classify("demo",legacy_row,legacy_registry,legacy_patch,{})
assert r["action"]=="KEEP_DIRECT",r

manual_disabled={"id":"demo","enabled":False,"disabledReason":"manual_off_test"}
assert module.restore_deprecated_nonfunctional_auto_off(manual_disabled,reg(),patch()) is False
assert manual_disabled["enabled"] is False

older_auto_off={
    "id":"demo","enabled":False,
    "disabledReason":"auto_off_current_architecture_nonfunctional",
    "disabledAt":"2026-11-14","purgeAfter":"2026-11-21","lifecycleState":"disabled-retained",
}
assert module.restore_deprecated_nonfunctional_auto_off(older_auto_off,reg(),patch()) is False
assert older_auto_off["enabled"] is False

# Bulk onboarding pending is non-active but distinct from disabled retention.
r=module.classify("demo",row(False),reg(),patch(),{},pending_onboarding=True)
assert r["action"]=="ONBOARDING_PENDING",r
assert r["repairEligible"] is False,r
assert r["authorityClass"]=="onboarding-pending",r

# Existing manual lifecycle decisions remain terminal.
r=module.classify("demo",row(False),reg(),patch(manual_off_reason="manual_off_test"),{})
assert r["action"]=="KEEP_DISABLED",r

assert "PROVIDER_AUTHORITY_BACKEND_SCOPE_V1" in SCRIPT.read_text(encoding="utf-8")
assert "PROVIDER_AUTHORITY_DIRECT_PROOF_V1" in SCRIPT.read_text(encoding="utf-8")
assert module.ROOT.joinpath("scripts/manage_provider_lifecycle.py").read_text(encoding="utf-8").find("RETENTION_DAYS = 7")>=0
print("provider authority arbiter contract ok")


# Current canonical census evidence remains useful diagnostic state, but the
# legacy helper no longer owns production lifecycle withdrawal merely because
# terminal proof is absent. Production freshness/certification owns that gate.
def census(status, *, tested=True, brain=True, repair=True):
    return {"status":status,"testedThisRun":tested,"brainCheckRequired":brain,"repairEligible":repair}

for status in ("REGRESSION PROVIDER","PARTIAL OK","CANDIDATE OK","ROUTE PROVEN","CHAIN REACHED","NO PROOF"):
    assert module.current_architecture_nonfunctional(census(status)) is True, status
for status in ("FULL OK","DISABLED"):
    assert module.current_architecture_nonfunctional(census(status)) is False, status
assert module.current_architecture_nonfunctional(census("ROUTE PROVEN",tested=False)) is False
assert module.current_architecture_nonfunctional(census("NO PROOF",brain=False)) is False
assert module.current_architecture_nonfunctional(census("CANDIDATE OK",repair=False)) is False
assert module.current_architecture_nonfunctional(census("PARTIAL OK",brain=False,repair=False)) is True
assert module.current_architecture_nonfunctional(census("PARTIAL OK",tested=False,brain=False,repair=False)) is False

manifest_row=row(True)
registry=reg()
nonfunctional_patch=patch()
reason=module.apply_disable(manifest_row,registry,nonfunctional_patch,"DISABLE_ARCHITECTURE_NONFUNCTIONAL")
assert reason=="auto_off_current_architecture_nonfunctional"
assert manifest_row["enabled"] is False
assert nonfunctional_patch["manifest_overrides"]["enabled"] is False
assert nonfunctional_patch["route_data_state"]=="off"
assert nonfunctional_patch["activation_eligible"] is False
assert "manual_off_reason" not in nonfunctional_patch
assert registry["manifest_status"]=="Désactivé"
assert "manual_off_reason" not in registry
print("current tested nonfunctional active-provider withdrawal contract passed")
