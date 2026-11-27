#!/usr/bin/env python3
"""Persist only sanitized, source-pinned catalogue-shape evidence for Brain.

This script never fetches network data. It accepts the already-sanitized output
of probe_catalogue_inline_live.py, verifies its exact official-TV parent and
current provider bytes, then stores a bounded prior-only diagnostic row.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
FLAGS=("proofAuthority","publicationAuthority","nativePlaybackAuthority","providerMutationAuthority")
ID=re.compile(r"^[a-z0-9][a-z0-9-]{0,95}$")
SHA40=re.compile(r"^[0-9a-f]{40}$")
SHA64=re.compile(r"^[0-9a-f]{64}$")
RUN=re.compile(r"^[0-9]{8,20}$")
HOST=re.compile(r"^(?=.{1,253}$)[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
SHAPES={"catalogue_inline_token_episode","legacy_external_episode_javascript","script_html_2xx","script_http_missing","unknown_response_shape"}
STATUS_CLASS={"2xx","3xx","4xx","5xx","other","transport"}
ROUTES={"catalogue","season_page","legacy_script","catalogue_search","token_resolver","resolved_target"}
TARGET_SHAPES={"hls_manifest","dash_manifest","media_binary","html_player","html_page","json","javascript","text","empty","redirect","http_error","transport_error","oversized"}
RESOLVER_CONTRACT="same-origin-api-lien-j-l-v1"


def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise ValueError("expected JSON object: "+str(path))
    return value


def current_provider_digest(root:Path, scope:str, provider:str)->str:
    manifest=load(root/scope)
    rows=[x for x in manifest.get("scrapers") or [] if isinstance(x,dict) and x.get("id")==provider]
    if len(rows)!=1: raise ValueError("provider manifest identity unavailable")
    relative=str(rows[0].get("filename") or "")
    if relative.startswith("../"): relative=relative[3:]
    if not relative.startswith("providers/") or ".." in Path(relative).parts:
        raise ValueError("invalid provider path")
    path=(root/relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("provider bytes unavailable")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_parent(root:Path, result:dict[str,Any])->None:
    provider=str(result.get("providerId") or "")
    fixture=str(result.get("fixture") or "")
    run=str(result.get("sourceRunId") or "")
    source=str(result.get("sourceNiakvioSha") or "")
    artifact=str(result.get("providerArtifactSha256") or "")
    scope=str(result.get("manifestScope") or "")
    if (not ID.fullmatch(provider) or not ID.fullmatch(fixture) or not RUN.fullmatch(run)
            or not SHA40.fullmatch(source) or not SHA64.fullmatch(artifact)
            or scope not in {"manifest.json","vf/manifest.json"}):
        raise ValueError("invalid source-probe parent identity")
    if current_provider_digest(root,scope,provider)!=artifact:
        raise ValueError("source-probe provider digest is not current")
    ledger=load(root/"automation/brain-android-tv-emulator-history.json")
    if (ledger.get("schemaVersion")!=1
            or ledger.get("authority")!="official-android-tv-emulator-diagnostic-only"
            or any(ledger.get(flag) is not False for flag in FLAGS)):
        raise ValueError("untrusted official-TV ledger")
    matches=[row for row in ledger.get("rows") or [] if (
        isinstance(row,dict)
        and row.get("provider")==provider and row.get("fixture")==fixture
        and str(row.get("nativeRunId") or "")==run
        and row.get("sourceNiakvioSha")==source
        and row.get("providerArtifactSha256")==artifact
        and row.get("manifestScope")==scope
        and row.get("appSelected") is True
        and row.get("readerEvidenceComplete") is True
        and row.get("nativeExtractionZeroObserved") is True
        and all(row.get(flag) is False for flag in FLAGS)
    )]
    if len(matches)!=1: raise ValueError("source-probe official-TV parent is not unique")


def sanitized_evidence(result:dict[str,Any])->list[dict[str,Any]]:
    observations=result.get("observations")
    count=result.get("probeRequestCount")
    if not isinstance(observations,list) or type(count) is not int or count!=len(observations) or not 1<=count<=18:
        raise ValueError("invalid source-probe observation count")
    by_host:dict[str,dict[str,Any]]={}
    for raw in observations:
        if not isinstance(raw,dict): raise ValueError("invalid source-probe observation")
        host=str(raw.get("originHost") or "")
        route=str(raw.get("routeKind") or "")
        status=raw.get("httpStatus")
        status_class=str(raw.get("httpStatusClass") or "")
        shape=str(raw.get("sourceShape") or "")
        if (not HOST.fullmatch(host) or route not in ROUTES or type(status) is not int
                or not 0<=status<=599 or status_class not in STATUS_CLASS or shape not in SHAPES):
            raise ValueError("unsafe source-probe observation")
        row=by_host.setdefault(host,{"originHost":host})
        if route=="catalogue": row["catalogueStatus"]=status
        elif route=="season_page":
            row["seasonPageStatus"]=status
            row["seasonSourceShape"]=shape
            for key in ("inlineSlotArrayObserved","opaqueLinkTokenObserved","jetonDeclarationObserved"):
                if type(raw.get(key)) is not bool: raise ValueError("invalid source shape flag")
                row[key]=raw[key]
        elif route=="legacy_script": row["legacyScriptStatus"]=status
        elif route=="token_resolver":
            contract=str(raw.get("resolverContract") or "")
            json_obj=raw.get("resolverJsonObjectObserved")
            url_field=raw.get("resolverUrlFieldObserved")
            https_url=raw.get("resolverHttpsUrlObserved")
            if (contract!=RESOLVER_CONTRACT or type(json_obj) is not bool
                    or type(url_field) is not bool or type(https_url) is not bool):
                raise ValueError("invalid token resolver evidence")
            row.update({
                "tokenResolverStatus":status,
                "tokenResolverContract":contract,
                "tokenResolverJsonObjectObserved":json_obj,
                "tokenResolverUrlFieldObserved":url_field,
                "tokenResolverHttpsUrlObserved":https_url,
            })
        elif route=="resolved_target":
            target_shape=str(raw.get("resolvedTargetShape") or "")
            direct=raw.get("resolvedTargetDirectMediaObserved")
            player=raw.get("resolvedTargetPlayerEmbedObserved")
            same_origin=raw.get("resolvedTargetSameOrigin")
            redirected=raw.get("resolvedTargetRedirectObserved")
            if (target_shape not in TARGET_SHAPES or type(direct) is not bool
                    or type(player) is not bool or type(same_origin) is not bool
                    or type(redirected) is not bool):
                raise ValueError("invalid resolved target evidence")
            row.update({
                "resolvedTargetStatus":status,
                "resolvedTargetShape":target_shape,
                "resolvedTargetDirectMediaObserved":direct,
                "resolvedTargetPlayerEmbedObserved":player,
                "resolvedTargetSameOrigin":same_origin,
                "resolvedTargetRedirectObserved":redirected,
            })
        elif route=="catalogue_search":
            links=raw.get("catalogueSearchLinkCount")
            exact=raw.get("catalogueSearchExactSlugPresent")
            candidate=str(raw.get("catalogueCandidateSlugUnverified") or "")
            overlap=raw.get("catalogueCandidateTokenOverlapPercent")
            if (type(links) is not int or not 0<=links<=32 or type(exact) is not bool
                    or (candidate and not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,125}",candidate))
                    or type(overlap) is not int or not 0<=overlap<=100):
                raise ValueError("invalid catalogue search evidence")
            row.update({"searchStatus":status,"searchLinkCount":links,
                        "searchExactSlugPresent":exact,
                        "candidateSlugUnverified":candidate,
                        "candidateTokenOverlapPercent":overlap})
        redirect=str(raw.get("redirectTargetHost") or "")
        curated=raw.get("redirectTargetCurated")
        if redirect:
            if not HOST.fullmatch(redirect) or curated is not True:
                raise ValueError("untrusted redirect evidence")
            row["redirectTargetHost"]=redirect
            row["redirectTargetCurated"]=True
    return list(by_host.values())[:3]


def build_row(root:Path,result:dict[str,Any],probe_run:str,probe_sha:str)->dict[str,Any]:
    if (result.get("schemaVersion")!=1
            or result.get("authority")!="independent-ci-source-shape-diagnostic-only"
            or result.get("independentNetworkNotOfficialClient") is not True
            or any(result.get(flag) is not False for flag in FLAGS)
            or any(result.get(k) is not False for k in (
                "sourceContractVerifiedOnOfficialTv","catalogueIdentityVerified","episodeIdentityVerified"
            ))):
        raise ValueError("source probe carries unsupported authority")
    if not RUN.fullmatch(probe_run) or not SHA40.fullmatch(probe_sha):
        raise ValueError("invalid probe run/source identity")
    validate_parent(root,result)
    evidence=sanitized_evidence(result)
    inline=result.get("inlineTokenResponseCount")
    resolver_probes=result.get("tokenResolverProbeCount")
    resolver_urls=result.get("tokenResolverJsonUrlCount")
    target_probes=result.get("resolvedTargetProbeCount",0)
    target_media=result.get("resolvedTargetDirectMediaCount",0)
    target_players=result.get("resolvedTargetPlayerPageCount",0)
    if type(inline) is not int or not 0<=inline<=int(result["probeRequestCount"]):
        raise ValueError("invalid inline source count")
    if (type(resolver_probes) is not int or type(resolver_urls) is not int
            or not 0<=resolver_urls<=resolver_probes<=3):
        raise ValueError("invalid token resolver counts")
    if (type(target_probes) is not int or type(target_media) is not int
            or type(target_players) is not int
            or not 0<=target_media<=target_probes<=3
            or not 0<=target_players<=target_probes<=3):
        raise ValueError("invalid resolved target counts")
    candidates=[
        (int(row.get("candidateTokenOverlapPercent") or 0),str(row.get("candidateSlugUnverified") or ""))
        for row in evidence if row.get("candidateSlugUnverified")
    ]
    candidates.sort(key=lambda x:(-x[0],len(x[1]),x[1]))
    next_slug=candidates[0][1] if candidates else ""
    input_slug=str(result.get("catalogueSlug") or "")
    if input_slug and not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,125}",input_slug):
        raise ValueError("invalid input catalogue slug")
    lead=("catalogue_inline_token_terminal_media_observed_unverified"
          if target_media>0 else "catalogue_inline_token_player_target_observed_unresolved"
          if target_players>0 else "catalogue_inline_token_target_observed_unresolved"
          if target_probes>0 else "catalogue_inline_token_resolver_observed_unverified"
          if resolver_urls>0 else "catalogue_slug_and_episode_source_contract_drift_candidate_unverified"
          if inline>0 else "catalogue_search_slug_mismatch_unverified"
          if next_slug and next_slug!=input_slug else "catalogue_source_contract_unresolved")
    return {
        "providerId":result["providerId"],"fixture":result["fixture"],
        "parentNativeRunId":str(result["sourceRunId"]),
        "parentNativeNiakvioSha":result["sourceNiakvioSha"],
        "parentNativeProviderArtifactSha256":result["providerArtifactSha256"],
        "manifestScope":result["manifestScope"],
        "probeRunIds":[probe_run],"latestProbeRunId":probe_run,
        "latestProbeSourceSha":probe_sha,"inputCatalogueSlug":input_slug,
        "independentNetworkNotOfficialClient":True,
        "probeRequestCount":int(result["probeRequestCount"]),
        "inlineTokenResponseCount":inline,
        "tokenResolverProbeCount":resolver_probes,
        "tokenResolverJsonUrlCount":resolver_urls,
        "tokenResolverContract":RESOLVER_CONTRACT if resolver_probes else None,
        "resolvedTargetProbeCount":target_probes,
        "resolvedTargetDirectMediaCount":target_media,
        "resolvedTargetPlayerPageCount":target_players,
        "sourceContractVerifiedOnOfficialTv":False,
        "catalogueIdentityVerified":False,"episodeIdentityVerified":False,
        "evidence":evidence,"leadHypothesis":lead,
        "candidateNextSlug":next_slug or None,"nextHypothesisRunId":None,
        "candidateMutationAllowed":False,"generatedByBrain":False,
        "modelExecuted":False,"validatedRepair":False,"publicationAllowed":False,
        **{flag:False for flag in FLAGS},
    }


def persist(history:dict[str,Any],row:dict[str,Any])->dict[str,Any]:
    expected={
        "schemaVersion":1,"authority":"independent-ci-source-shape-diagnostic-only",
        "primaryClient":"independent-github-runner-not-official-android-tv",
    }
    if any(history.get(k)!=v for k,v in expected.items()) or any(history.get(f) is not False for f in FLAGS):
        raise ValueError("invalid source-probe history envelope")
    rows=[x for x in history.get("rows") or [] if isinstance(x,dict)]
    key=(row["providerId"],row["fixture"],row["parentNativeRunId"],row["parentNativeProviderArtifactSha256"],row["latestProbeRunId"])
    rows=[x for x in rows if (x.get("providerId"),x.get("fixture"),str(x.get("parentNativeRunId") or ""),
                              x.get("parentNativeProviderArtifactSha256"),str(x.get("latestProbeRunId") or ""))!=key]
    rows.append(row)
    # Keep useful negatives/history but bound growth deterministically.
    history=dict(history); history["rows"]=rows[-80:]
    return history


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--result",type=Path,required=True)
    p.add_argument("--history",type=Path,default=ROOT/"automation/brain-catalogue-source-probe-history.json")
    p.add_argument("--probe-run-id",required=True)
    p.add_argument("--probe-source-sha",required=True)
    p.add_argument("--root",type=Path,default=ROOT)
    args=p.parse_args()
    result=load(args.result); history=load(args.history)
    row=build_row(args.root.resolve(),result,args.probe_run_id,args.probe_source_sha)
    out=persist(history,row)
    args.history.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("FIELD_BRAIN_SOURCE_PROBE_PERSIST provider=%s native_run=%s probe_run=%s inline=%d authority=false" % (
        row["providerId"],row["parentNativeRunId"],row["latestProbeRunId"],row["inlineTokenResponseCount"]))
    return 0


if __name__=="__main__": raise SystemExit(main())
