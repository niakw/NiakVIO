#!/usr/bin/env python3
"""Source-contract negative memory must stop generic executor fallback, not repair."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/fill_brain_learning_guidance_gaps.py"
spec=importlib.util.spec_from_file_location("source_guidance_gap",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

RUN="44781039914"
SHA="a"*40
PUBSHA="b"*40
FIXTURE="test-s01e01"
PROVIDER="sample"
DATA=b"synthetic immutable provider JS\n"
DIGEST=hashlib.sha256(DATA).hexdigest()
FLAGS={name:False for name in ("proofAuthority","publicationAuthority",
                               "nativePlaybackAuthority","providerMutationAuthority")}

with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    (root/"providers").mkdir()
    (root/"providers/sample.js").write_bytes(DATA)
    manifest={"scrapers":[{"id":PROVIDER,"filename":"providers/sample.js"}]}
    native_row={
        "provider":PROVIDER,"fixture":FIXTURE,"nativeRunId":RUN,
        "sourceNiakvioSha":SHA,"providerArtifactSha256":DIGEST,
        "manifestScope":"manifest.json","appSelected":True,
        "readerEvidenceComplete":True,"nativeExtractionZeroObserved":True,
        "nativeSourceScriptShapePatterns":["script_http_missing","script_html_2xx"],
        **FLAGS,
    }
    native={
        "schemaVersion":1,"authority":"official-android-tv-emulator-diagnostic-only",
        "primaryClient":"tv","rows":[native_row],**FLAGS,
    }
    probe_row={
        "providerId":PROVIDER,"fixture":FIXTURE,
        "parentNativeRunId":RUN,"parentNativeNiakvioSha":SHA,
        "parentNativeProviderArtifactSha256":DIGEST,"manifestScope":"manifest.json",
        "latestProbeRunId":"44798438960","latestProbeSourceSha":PUBSHA,
        "inputCatalogueSlug":"test",
        "inlineTokenResponseCount":1,"probeRequestCount":13,
        "tokenResolverProbeCount":1,"tokenResolverJsonUrlCount":1,
        "tokenResolverContract":"same-origin-api-lien-j-l-v1",
        "resolvedTargetProbeCount":1,"resolvedTargetDirectMediaCount":0,
        "resolvedTargetPlayerPageCount":1,
        "independentNetworkNotOfficialClient":True,
        "sourceContractVerifiedOnOfficialTv":False,
        "catalogueIdentityVerified":False,"episodeIdentityVerified":False,
        "candidateMutationAllowed":False,"publicationAllowed":False,
        "generatedByBrain":False,"modelExecuted":False,"validatedRepair":False,
        "evidence":[{
            "originHost":"example.test","seasonPageStatus":200,
            "seasonSourceShape":"catalogue_inline_token_episode",
            "inlineSlotArrayObserved":True,"opaqueLinkTokenObserved":True,
            "jetonDeclarationObserved":True,
            "tokenResolverStatus":200,
            "tokenResolverContract":"same-origin-api-lien-j-l-v1",
            "tokenResolverJsonObjectObserved":True,
            "tokenResolverUrlFieldObserved":True,
            "tokenResolverHttpsUrlObserved":True,
            "resolvedTargetStatus":200,"resolvedTargetShape":"html_player",
            "resolvedTargetDirectMediaObserved":False,
            "resolvedTargetPlayerEmbedObserved":True,
            "resolvedTargetSameOrigin":False,
            "resolvedTargetRedirectObserved":False,
        }],
        **FLAGS,
    }
    history={
        "schemaVersion":1,"authority":"independent-ci-source-shape-diagnostic-only",
        "primaryClient":"independent-github-runner-not-official-android-tv",
        "rows":[probe_row],**FLAGS,
    }
    frontier=mod.attested_source_contract_frontier(history,native,manifest,root)
    assert frontier=={"sample"},frontier
    resolver=mod.attested_source_resolver_frontier(history,native,manifest,root)
    assert resolver=={"sample"},resolver
    player=mod.attested_source_player_target_frontier(history,native,manifest,root)
    assert player=={"sample"},player
    released_source_frontier=frontier-player
    assert released_source_frontier==set()
    old_guidance={
        "sourceSha":"a"*40,"brainLlmSha":"a"*40,"schemaVersion":2,
        "providerCount":1,
        "rows":[{
            "providerId":"sample","targetLayer":"provider",
            "profile":"adaptive_runtime_recovery",
            "strategy":"meta-gap-unknown-runtime-composition",
            "experimentFingerprint":"f"*64,
            "priorOnly":True,"experiment":{},
        }],
    }
    census={"repairQueue":["sample"],"providers":[{
        "provider":"sample","status":"ROUTE PROVEN",
        "dominantIssue":"route_proven_gap","evidenceDepth":["route_proven"],
    }]}
    out,added=mod.fill(
        old_guidance,providers=["sample"],current_sha="c"*40,
        census=census,memory={"entries":[]},source_frontier=frontier,
    )
    assert not added and out["providerCount"]==0 and out["rows"]==[],out
    released_guidance, released_added=mod.fill(
        old_guidance,providers=["sample"],current_sha="c"*40,
        census=census,memory={"entries":[]},source_frontier=released_source_frontier,
    )
    assert released_guidance["providerCount"]>=1,released_guidance
    assert any(
        row.get("providerId")=="sample"
        for row in released_guidance["rows"]
        if isinstance(row,dict)
    ),released_guidance
    released_report=mod.exhaustion_report(
        providers=["sample"],current_sha="c"*40,census=census,
        memory={"entries":[]},source_frontier=released_source_frontier,
    )
    assert released_report["deferredSourceContractProviders"]==[],released_report
    report=mod.exhaustion_report(
        providers=["sample"],current_sha="c"*40,census=census,
        memory={"entries":[]},source_frontier=frontier,
    )
    assert report["architectureForceRecommended"] is True
    assert report["deferredSourceContractProviders"]==["sample"],report
    assert report["sourceContractExecutorStatus"]=="new_family_required"
    for forged in (
        {"latestProbeRunId":"nonsense"},
        {"parentNativeRunId":"44781039915"},
        {"parentNativeProviderArtifactSha256":"f"*64},
        {"sourceContractVerifiedOnOfficialTv":True},
        {"candidateMutationAllowed":True},
        {"inlineTokenResponseCount":0},
        {"evidence":[]},
    ):
        edited=json.loads(json.dumps(history))
        edited["rows"][0].update(forged)
        assert not mod.attested_source_contract_frontier(
            edited,native,manifest,root
        ),forged

    for forged_player in (
        {"resolvedTargetProbeCount":0},
        {"evidence":[{**probe_row["evidence"][0],"resolvedTargetStatus":403}]},
        {"evidence":[{**probe_row["evidence"][0],"resolvedTargetShape":"json"}]},
        {"evidence":[{**probe_row["evidence"][0],"resolvedTargetDirectMediaObserved":True}]},
        {"evidence":[{**probe_row["evidence"][0],"resolvedTargetPlayerEmbedObserved":False}]},
    ):
        edited=json.loads(json.dumps(history))
        edited["rows"][0].update(forged_player)
        assert not mod.attested_source_player_target_frontier(
            edited,native,manifest,root
        ),forged_player

    for forged_resolver in (
        {"tokenResolverProbeCount":0},
        {"tokenResolverJsonUrlCount":0},
        {"tokenResolverContract":"other"},
        {"evidence":[{**probe_row["evidence"][0],"tokenResolverStatus":403}]},
        {"evidence":[{**probe_row["evidence"][0],"tokenResolverHttpsUrlObserved":False}]},
    ):
        edited=json.loads(json.dumps(history))
        edited["rows"][0].update(forged_resolver)
        assert not mod.attested_source_resolver_frontier(
            edited,native,manifest,root
        ),forged_resolver
    incompatible=json.loads(json.dumps(native))
    incompatible["rows"][0]["nativeExtractionZeroObserved"]=False
    assert not mod.attested_source_contract_frontier(history,incompatible,manifest,root)
    (root/"providers/sample.js").write_bytes(b"changed")
    assert not mod.attested_source_contract_frontier(history,native,manifest,root)
print("Source-contract frontier: native parent + immutable current JS, zero recycled guidance, architecture deferred, forged inputs rejected")
