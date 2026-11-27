#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"scripts/persist_brain_catalogue_source_probe.py"
spec=importlib.util.spec_from_file_location("persist_source_probe",SRC)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
FLAGS={x:False for x in mod.FLAGS}

with tempfile.TemporaryDirectory() as td:
    root=Path(td);(root/"providers").mkdir(parents=True);(root/"automation").mkdir()
    data=b"current provider bytes\n";provider_file=root/"providers/sample.js";provider_file.write_bytes(data)
    digest=hashlib.sha256(data).hexdigest()
    (root/"manifest.json").write_text(json.dumps({"scrapers":[{"id":"sample","filename":"providers/sample.js"}]}))
    native_row={"provider":"sample","fixture":"mushoku-s01e01","nativeRunId":"45321345600",
        "sourceNiakvioSha":"a"*40,"providerArtifactSha256":digest,"manifestScope":"manifest.json",
        "appSelected":True,"readerEvidenceComplete":True,"nativeExtractionZeroObserved":True,**FLAGS}
    native={"schemaVersion":1,"authority":"official-android-tv-emulator-diagnostic-only",
        "primaryClient":"tv","rows":[native_row],**FLAGS}
    (root/"automation/brain-android-tv-emulator-history.json").write_text(json.dumps(native))
    result={"schemaVersion":1,"authority":"independent-ci-source-shape-diagnostic-only",
        "providerId":"sample","fixture":"mushoku-s01e01","sourceRunId":"45321345600",
        "sourceNiakvioSha":"a"*40,"providerArtifactSha256":digest,"manifestScope":"manifest.json",
        "catalogueSlug":"mushoku-tensei","independentNetworkNotOfficialClient":True,
        "catalogueIdentityVerified":False,"episodeIdentityVerified":False,
        "sourceContractVerifiedOnOfficialTv":False,"probeRequestCount":6,"inlineTokenResponseCount":1,
        "tokenResolverProbeCount":1,"tokenResolverJsonUrlCount":1,
        "resolvedTargetProbeCount":1,"resolvedTargetDirectMediaCount":0,
        "resolvedTargetPlayerPageCount":1,
        "observations":[
          {"originHost":"example.test","routeKind":"catalogue","httpStatus":200,"httpStatusClass":"2xx",
           "sourceShape":"script_html_2xx","redirectTargetHost":"","redirectTargetCurated":False},
          {"originHost":"example.test","routeKind":"season_page","httpStatus":200,"httpStatusClass":"2xx",
           "sourceShape":"catalogue_inline_token_episode","inlineSlotArrayObserved":True,
           "opaqueLinkTokenObserved":True,"jetonDeclarationObserved":True,
           "redirectTargetHost":"","redirectTargetCurated":False},
          {"originHost":"example.test","routeKind":"legacy_script","httpStatus":404,"httpStatusClass":"4xx",
           "sourceShape":"script_http_missing","redirectTargetHost":"","redirectTargetCurated":False},
          {"originHost":"example.test","routeKind":"token_resolver","httpStatus":200,"httpStatusClass":"2xx",
           "sourceShape":"unknown_response_shape","resolverContract":"same-origin-api-lien-j-l-v1",
           "resolverJsonObjectObserved":True,"resolverUrlFieldObserved":True,
           "resolverHttpsUrlObserved":True,"redirectTargetHost":"","redirectTargetCurated":False},
          {"originHost":"example.test","routeKind":"resolved_target","httpStatus":200,"httpStatusClass":"2xx",
           "sourceShape":"unknown_response_shape","resolvedTargetShape":"html_player",
           "resolvedTargetDirectMediaObserved":False,"resolvedTargetPlayerEmbedObserved":True,
           "resolvedTargetSameOrigin":False,"resolvedTargetRedirectObserved":False,
           "redirectTargetHost":"","redirectTargetCurated":False},
          {"originHost":"example.test","routeKind":"catalogue_search","httpStatus":200,"httpStatusClass":"2xx",
           "sourceShape":"script_html_2xx","catalogueSearchLinkCount":1,
           "catalogueSearchExactSlugPresent":True,"catalogueCandidateSlugUnverified":"mushoku-tensei",
           "catalogueCandidateTokenOverlapPercent":100,"redirectTargetHost":"","redirectTargetCurated":False},
        ],**FLAGS}
    row=mod.build_row(root,result,"45323000000","b"*40)
    assert row["inlineTokenResponseCount"]==1
    assert row["leadHypothesis"]=="catalogue_inline_token_player_target_observed_unresolved"
    assert row["tokenResolverProbeCount"]==1 and row["tokenResolverJsonUrlCount"]==1
    assert row["resolvedTargetProbeCount"]==1
    assert row["resolvedTargetPlayerPageCount"]==1
    assert row["tokenResolverContract"]=="same-origin-api-lien-j-l-v1"
    assert row["evidence"]==[{"originHost":"example.test","catalogueStatus":200,
        "seasonPageStatus":200,"seasonSourceShape":"catalogue_inline_token_episode",
        "inlineSlotArrayObserved":True,"opaqueLinkTokenObserved":True,"jetonDeclarationObserved":True,
        "legacyScriptStatus":404,"tokenResolverStatus":200,
        "tokenResolverContract":"same-origin-api-lien-j-l-v1",
        "tokenResolverJsonObjectObserved":True,"tokenResolverUrlFieldObserved":True,
        "tokenResolverHttpsUrlObserved":True,
        "resolvedTargetStatus":200,"resolvedTargetShape":"html_player",
        "resolvedTargetDirectMediaObserved":False,"resolvedTargetPlayerEmbedObserved":True,
        "resolvedTargetSameOrigin":False,"resolvedTargetRedirectObserved":False,
        "searchStatus":200,"searchLinkCount":1,
        "searchExactSlugPresent":True,"candidateSlugUnverified":"mushoku-tensei",
        "candidateTokenOverlapPercent":100}]
    envelope={"schemaVersion":1,"authority":"independent-ci-source-shape-diagnostic-only",
        "primaryClient":"independent-github-runner-not-official-android-tv","rows":[],**FLAGS}
    saved=mod.persist(envelope,row);saved2=mod.persist(saved,row)
    assert saved2["rows"]==[row]
    rendered=json.dumps(saved2)
    for forbidden in ("<html","https://","lien:","epsJeton","PRIVATE_TOKEN","PRIVATE_JETON","media.invalid"):
        assert forbidden not in rendered

    forged=json.loads(json.dumps(result));forged["publicationAuthority"]=True
    try:mod.build_row(root,forged,"45323000000","b"*40)
    except ValueError:pass
    else:raise AssertionError("authority-bearing probe persisted")
    forged=json.loads(json.dumps(result));forged["observations"][1]["originHost"]="https://evil.test"
    try:mod.build_row(root,forged,"45323000000","b"*40)
    except ValueError:pass
    else:raise AssertionError("URL-shaped origin persisted")
    provider_file.write_bytes(b"drifted")
    try:mod.build_row(root,result,"45323000000","b"*40)
    except ValueError:pass
    else:raise AssertionError("stale provider bytes persisted")
print("Brain catalogue source probe persistence is exact-parent, sanitized and idempotent")
