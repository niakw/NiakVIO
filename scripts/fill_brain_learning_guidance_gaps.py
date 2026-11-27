#!/usr/bin/env python3
"""Fill or advance targeted Learning guidance with deterministic Brain meta-gap synthesis.

This is a hypothesis-only bridge: it never mutates provider/publication bytes and
never grants proof/publication authority. It is used only after cached/Qwen rows
were sanitized and negative-memory filtered. Targeted providers may receive the
next bounded already-sandboxed executor selected from current census and canonical
Repair memory even when an older, now-causally-exhausted row for that provider is
already present. This closes Learning-runtime -> persisted-guidance handoff.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR=Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0,str(SCRIPT_DIR))

from brain_layers.declarative_gap_strategy import synthesize_rows

SOURCE_SHAPES = frozenset({"script_http_missing", "script_html_2xx"})
SOURCE_INLINE = "catalogue_inline_token_episode"
SOURCE_RESOLVER_CONTRACT = "same-origin-api-lien-j-l-v1"
FRONTIER_FLAGS = (
    "proofAuthority", "publicationAuthority",
    "nativePlaybackAuthority", "providerMutationAuthority",
)


def attested_source_contract_frontier(
    source_history: dict[str, Any],
    native_history: dict[str, Any],
    manifest: dict[str, Any],
    root: Path,
) -> set[str]:
    """A read-only CI source witness can defer generic executors, never repair.

    Require current published JS bytes and exact official-TV native parent.
    Missing/forged/stale evidence must not interfere with other providers.
    """
    if (
        not isinstance(source_history, dict)
        or source_history.get("schemaVersion") != 1
        or source_history.get("authority") != "independent-ci-source-shape-diagnostic-only"
        or source_history.get("primaryClient")
            != "independent-github-runner-not-official-android-tv"
        or not isinstance(native_history, dict)
        or native_history.get("schemaVersion") != 1
        or native_history.get("authority") != "official-android-tv-emulator-diagnostic-only"
        or native_history.get("primaryClient") != "tv"
        or any(source_history.get(k) is not False for k in FRONTIER_FLAGS)
        or any(native_history.get(k) is not False for k in FRONTIER_FLAGS)
        or not isinstance(manifest, dict)
    ):
        return set()
    rows = manifest.get("scrapers")
    if not isinstance(rows, list):
        return set()
    owned: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        provider = canon(row.get("id"))
        relative = str(row.get("filename") or "")
        if (not re.fullmatch(r"[a-z0-9][a-z0-9_-]{1,79}", provider)
                or not relative.startswith("providers/") or not relative.endswith(".js")
                or ".." in Path(relative).parts):
            continue
        try:
            file = (root / relative).resolve()
            file.relative_to(root.resolve())
            if file.is_file():
                owned[provider] = hashlib.sha256(file.read_bytes()).hexdigest()
        except (ValueError, OSError):
            continue
    out: set[str] = set()
    native = native_history.get("rows")
    if not isinstance(native, list):
        return out
    for row in (source_history.get("rows") or [])[-1400:]:
        if not isinstance(row, dict):
            continue
        provider = canon(row.get("providerId"))
        artifact = str(row.get("parentNativeProviderArtifactSha256") or "").lower()
        native_run = str(row.get("parentNativeRunId") or "")
        source_sha = str(row.get("parentNativeNiakvioSha") or "")
        fixture = str(row.get("fixture") or "")
        scope = str(row.get("manifestScope") or "manifest.json")
        evidence = row.get("evidence")
        inline_count = row.get("inlineTokenResponseCount")
        requests = row.get("probeRequestCount")
        probe_run = str(row.get("latestProbeRunId") or "")
        probe_sha = str(row.get("latestProbeSourceSha") or "")
        if (owned.get(provider) != artifact
                or not re.fullmatch(r"[a-f0-9]{64}", artifact)
                or not re.fullmatch(r"[a-f0-9]{40}", source_sha)
                or not re.fullmatch(r"[0-9]{8,20}", native_run)
                or not re.fullmatch(r"[0-9]{8,20}", probe_run)
                or not re.fullmatch(r"[a-f0-9]{40}", probe_sha)
                or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,95}", fixture)
                or scope != "manifest.json"
                or type(requests) is not int or not 1 <= requests <= 18
                or type(inline_count) is not int or not 1 <= inline_count <= requests
                or row.get("independentNetworkNotOfficialClient") is not True
                or row.get("sourceContractVerifiedOnOfficialTv") is not False
                or row.get("catalogueIdentityVerified") is not False
                or row.get("episodeIdentityVerified") is not False
                or row.get("candidateMutationAllowed") is not False
                or row.get("publicationAllowed") is not False
                or row.get("generatedByBrain") is not False
                or row.get("modelExecuted") is not False
                or row.get("validatedRepair") is not False
                or any(row.get(k) is not False for k in FRONTIER_FLAGS)
                or not isinstance(evidence, list)
                or not any(
                    isinstance(e, dict)
                    and e.get("seasonSourceShape") == SOURCE_INLINE
                    and e.get("seasonPageStatus") == 200
                    and e.get("inlineSlotArrayObserved") is True
                    and e.get("opaqueLinkTokenObserved") is True
                    and e.get("jetonDeclarationObserved") is True
                    for e in evidence
                )):
            continue
        if any(
            isinstance(native_row, dict)
            and canon(native_row.get("provider")) == provider
            and native_row.get("nativeRunId") == native_run
            and native_row.get("sourceNiakvioSha") == source_sha
            and native_row.get("providerArtifactSha256") == artifact
            and native_row.get("fixture") == fixture
            and native_row.get("manifestScope") == scope
            and native_row.get("appSelected") is True
            and native_row.get("readerEvidenceComplete") is True
            and native_row.get("nativeExtractionZeroObserved") is True
            and any(x in SOURCE_SHAPES
                    for x in native_row.get("nativeSourceScriptShapePatterns") or [])
            and all(native_row.get(k) is False for k in FRONTIER_FLAGS)
            for native_row in native[:1400]
        ):
            out.add(provider)
    return out


def attested_source_resolver_frontier(
    source_history: dict[str, Any],
    native_history: dict[str, Any],
    manifest: dict[str, Any],
    root: Path,
) -> set[str]:
    """Return only exact-parent source rows that also proved the sanitized resolver shape.

    This remains diagnostic-only: the underlying source frontier still requires the
    immutable current provider bytes and exact official-TV zero-extraction parent.
    No token, identifier, response body or resolved URL is consumed here.
    """
    if not isinstance(source_history, dict):
        return set()
    eligible: list[dict[str, Any]] = []
    for row in source_history.get("rows") or []:
        if not isinstance(row, dict):
            continue
        probes = row.get("tokenResolverProbeCount")
        urls = row.get("tokenResolverJsonUrlCount")
        if (
            type(probes) is not int or type(urls) is not int
            or not 1 <= probes <= 3 or not 1 <= urls <= probes
            or row.get("tokenResolverContract") != SOURCE_RESOLVER_CONTRACT
        ):
            continue
        evidence = row.get("evidence")
        if not isinstance(evidence, list) or not any(
            isinstance(e, dict)
            and e.get("seasonSourceShape") == SOURCE_INLINE
            and e.get("seasonPageStatus") == 200
            and e.get("inlineSlotArrayObserved") is True
            and e.get("opaqueLinkTokenObserved") is True
            and e.get("jetonDeclarationObserved") is True
            and e.get("tokenResolverStatus") == 200
            and e.get("tokenResolverContract") == SOURCE_RESOLVER_CONTRACT
            and e.get("tokenResolverJsonObjectObserved") is True
            and e.get("tokenResolverUrlFieldObserved") is True
            and e.get("tokenResolverHttpsUrlObserved") is True
            for e in evidence
        ):
            continue
        eligible.append(row)
    narrowed = dict(source_history)
    narrowed["rows"] = eligible
    return attested_source_contract_frontier(
        narrowed, native_history, manifest, root,
    )


def attested_source_player_target_frontier(
    source_history: dict[str, Any],
    native_history: dict[str, Any],
    manifest: dict[str, Any],
    root: Path,
) -> set[str]:
    """Return exact-parent providers whose resolver target is a player page.

    This frontier is deeper than resolver availability: the same sanitized row
    must prove resolver shape plus a 2xx HTML player target with an observed
    player embed and no direct media. It remains diagnostic-only and carries no
    playback, identity, mutation or publication authority.
    """
    if not isinstance(source_history, dict):
        return set()
    eligible: list[dict[str, Any]] = []
    for row in source_history.get("rows") or []:
        if not isinstance(row, dict):
            continue
        target_probes = row.get("resolvedTargetProbeCount")
        if type(target_probes) is not int or not 1 <= target_probes <= 3:
            continue
        evidence = row.get("evidence")
        if not isinstance(evidence, list) or not any(
            isinstance(item, dict)
            and item.get("seasonSourceShape") == SOURCE_INLINE
            and item.get("seasonPageStatus") == 200
            and item.get("tokenResolverStatus") == 200
            and item.get("tokenResolverContract") == SOURCE_RESOLVER_CONTRACT
            and item.get("tokenResolverJsonObjectObserved") is True
            and item.get("tokenResolverUrlFieldObserved") is True
            and item.get("tokenResolverHttpsUrlObserved") is True
            and type(item.get("resolvedTargetStatus")) is int
            and 200 <= item.get("resolvedTargetStatus") < 300
            and item.get("resolvedTargetShape") == "html_player"
            and item.get("resolvedTargetDirectMediaObserved") is False
            and item.get("resolvedTargetPlayerEmbedObserved") is True
            and type(item.get("resolvedTargetSameOrigin")) is bool
            and type(item.get("resolvedTargetRedirectObserved")) is bool
            for item in evidence
        ):
            continue
        eligible.append(row)
    narrowed = dict(source_history)
    narrowed["rows"] = eligible
    return attested_source_resolver_frontier(
        narrowed, native_history, manifest, root,
    )


ROW_FIELDS={
    "providerId","failureClass","targetLayer","strategy","profile",
    "confidence","priorOnly","experiment","experimentFingerprint",
}
SHA40=re.compile(r"^[0-9a-f]{40}$")


def canon(value:object)->str:
    return str(value or "").strip().casefold().replace("_","-")


def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict) or not isinstance(value.get("rows"),list):
        raise ValueError(f"invalid guidance payload: {path}")
    return value


def merge_memory_payloads(payloads:list[dict[str,Any]])->dict[str,Any]:
    """Join sanitized Repair + Learning experiment ledgers for hypothesis rotation.

    Duplicate rows are harmless to the declarative strategy because failed
    fingerprints/executed-profile accounting is set based. Keep the original
    rows intact so this bridge cannot invent execution authority or proof.
    """
    entries:list[dict[str,Any]]=[]
    for payload in payloads:
        if not isinstance(payload,dict):
            continue
        for raw in payload.get("entries") or []:
            if isinstance(raw,dict):
                entries.append(json.loads(json.dumps(raw)))
        experiment=payload.get("experimentMemory")
        if isinstance(experiment,dict):
            for raw in experiment.get("entries") or []:
                if isinstance(raw,dict):
                    entries.append(json.loads(json.dumps(raw)))
    return {"entries":entries}


def public_row(raw:dict[str,Any])->dict[str,Any]:
    row={key:raw.get(key) for key in ROW_FIELDS}
    if (
        not canon(row.get("providerId"))
        or row.get("targetLayer")!="provider"
        or row.get("priorOnly") is not True
        or not str(row.get("profile") or "").strip()
        or not re.fullmatch(r"[0-9a-f]{64}",str(row.get("experimentFingerprint") or "").strip().casefold())
        or not isinstance(row.get("experiment"),dict)
    ):
        raise ValueError("unsafe synthesized Learning guidance row")
    return row


def fill(
    payload:dict[str,Any],
    *,
    providers:list[str],
    current_sha:str,
    census:dict[str,Any],
    memory:dict[str,Any],
    source_frontier:set[str] | frozenset[str] = frozenset(),
)->tuple[dict[str,Any],list[str]]:
    wanted=[]
    seen_wanted=set()
    for raw in providers:
        provider=canon(raw)
        if provider and provider not in seen_wanted:
            seen_wanted.add(provider);wanted.append(provider)
    out=json.loads(json.dumps(payload))
    # An exact-byte, native-parent-attested inline episode contract is a
    # *different causal family*. Do not recycle generic route/traversal
    # executor guidance before a dedicated source-family Lego exists.
    rows=[row for row in out.get("rows") or []
          if isinstance(row,dict) and canon(row.get("providerId")) not in source_frontier]
    existing_keys={
        (
            canon(row.get("providerId")),
            str(row.get("profile") or "").strip().casefold(),
            str(row.get("experimentFingerprint") or "").strip().casefold(),
        )
        for row in rows
    }

    synthesized=synthesize_rows(census=census,memory=memory,current_sha=current_sha,max_rows=128)
    by_provider={}
    for raw in synthesized:
        if not isinstance(raw,dict):
            continue
        provider=canon(raw.get("providerId"))
        if provider in seen_wanted and provider not in by_provider:
            by_provider[provider]=public_row(raw)

    added=[]
    for provider in wanted:
        if provider in source_frontier:
            continue
        row=by_provider.get(provider)
        if row is None:
            continue
        key=(
            provider,
            str(row.get("profile") or "").strip().casefold(),
            str(row.get("experimentFingerprint") or "").strip().casefold(),
        )
        if key in existing_keys:
            continue
        rows.append(row)
        existing_keys.add(key)
        added.append(provider)
    out["rows"]=rows
    out["providerCount"]=len({canon(row.get("providerId")) for row in rows if canon(row.get("providerId"))})
    if SHA40.fullmatch(str(current_sha or "").strip().casefold()):
        out["sourceSha"]=str(current_sha).strip().casefold()
    return out,added


def exhaustion_report(
    *,
    providers:list[str],
    current_sha:str,
    census:dict[str,Any],
    memory:dict[str,Any],
    source_frontier:set[str] | frozenset[str] = frozenset(),
)->dict[str,Any]:
    wanted=[]
    seen=set()
    for raw in providers:
        provider=canon(raw)
        if provider and provider not in seen:
            seen.add(provider);wanted.append(provider)
    repair_queue={canon(x) for x in census.get("repairQueue") or [] if canon(x)}
    synthesized=synthesize_rows(census=census,memory=memory,current_sha=current_sha,max_rows=128)
    synthesized_providers={
        canon(row.get("providerId"))
        for row in synthesized
        if isinstance(row,dict) and canon(row.get("providerId"))
    }
    exhausted=[
        provider for provider in wanted
        if provider in repair_queue
        and (provider not in synthesized_providers or provider in source_frontier)
    ]
    deferred=[p for p in wanted if p in repair_queue and p in source_frontier]
    return {
        "schemaVersion":1,
        "role":"architecture-escalation-signal-only",
        "publicationAuthority":False,
        "providerMutationAuthority":False,
        "requestedProviders":wanted,
        "synthesizedProviders":sorted(synthesized_providers & set(wanted)),
        "exhaustedProviders":exhausted,
        "deferredSourceContractProviders":deferred,
        "sourceContractExecutorStatus":("new_family_required" if deferred else "not_attested"),
        "architectureForceRecommended":bool(exhausted),
    }


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--provider",action="append",default=[])
    p.add_argument("--providers",default="")
    p.add_argument("--current-sha",required=True)
    p.add_argument("--census",type=Path,default=Path("automation/provider-census-status.json"))
    p.add_argument("--memory",type=Path,action="append",default=[])
    p.add_argument("--report",type=Path)
    a=p.parse_args()
    providers=[*a.provider,*str(a.providers or "").split(",")]
    payload=load(a.input)
    census=json.loads(a.census.read_text(encoding="utf-8"))
    memory_paths=list(a.memory or [Path("automation/brain-repair-memory.json")])
    memory_payloads=[]
    for memory_path in memory_paths:
        value=json.loads(memory_path.read_text(encoding="utf-8"))
        if not isinstance(value,dict):
            raise ValueError(f"invalid Brain memory payload: {memory_path}")
        memory_payloads.append(value)
    memory=merge_memory_payloads(memory_payloads)
    def optional_json(path:Path)->dict[str,Any]:
        try:
            value=json.loads(path.read_text(encoding="utf-8"))
            return value if isinstance(value,dict) else {}
        except (OSError,ValueError):
            return {}
    root=Path(__file__).resolve().parents[1]
    source_history=optional_json(root/"automation/brain-catalogue-source-probe-history.json")
    native_history=optional_json(root/"automation/brain-android-tv-emulator-history.json")
    manifest=optional_json(root/"manifest.json")
    source_frontier=attested_source_contract_frontier(
        source_history,native_history,manifest,root,
    )
    player_target_frontier=attested_source_player_target_frontier(
        source_history,native_history,manifest,root,
    )
    # The source-family defer gate is monotone. Once exact-parent evidence has
    # advanced through the resolver to a player target, generic source-family
    # synthesis is no longer the owner; current player/media guidance must be
    # allowed to reach the planner.
    deferred_source_frontier=set(source_frontier)-set(player_target_frontier)
    output,added=fill(payload,providers=providers,current_sha=a.current_sha,census=census,memory=memory,
                      source_frontier=deferred_source_frontier)
    report=exhaustion_report(
        providers=providers,current_sha=a.current_sha,census=census,memory=memory,
        source_frontier=deferred_source_frontier
    )
    report["playerTargetReleasedProviders"]=sorted(
        set(player_target_frontier) & {canon(x) for x in providers if canon(x)}
    )
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(output,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    if a.report is not None:
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(
        "FIELD_BRAIN_LEARNING_GUIDANCE_GAP_FILL "
        f"requested={len({canon(x) for x in providers if canon(x)})} "
        f"advanced={len(added)} providers={','.join(added) or 'none'} "
        f"exhausted={len(report['exhaustedProviders'])} "
        f"exhausted_providers={','.join(report['exhaustedProviders']) or 'none'} "
        f"final={output.get('providerCount',0)} "
        f"deferred_source_contract={','.join(report['deferredSourceContractProviders']) or 'none'} "
        f"released_player_target={','.join(report['playerTargetReleasedProviders']) or 'none'}"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
