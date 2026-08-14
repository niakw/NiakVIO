#!/usr/bin/env python3
"""Bound global catalogue fallback work on native QuickJS clients.

The global catalogue fallback historically relied on AbortSignal + a wall-clock
budget. In official Nuvio native runtimes (Desktop, Mobile Android and Android TV),
``__native_fetch`` is a synchronous host call, so JS AbortSignal cannot reliably
interrupt an in-flight HTTP request.

The native policy therefore limits request *count*, but it must not simply take the
first N searches: catalogue aliases are intentionally multilingual and target sites
expose several search routes. The current revision samples alias x route combinations
round-robin and interleaves discovered and guessed candidate pages. This preserves
recovery diversity while keeping the number of blocking host calls finite.
"""
from __future__ import annotations

from typing import Any

MARKER = "NUVIO_NATIVE_CATALOGUE_RECOVERY_BUDGET_V2"
LEGACY_MARKER = "NUVIO_NATIVE_CATALOGUE_RECOVERY_BUDGET_V1"
CATALOGUE_MARKER = "NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2"
WRAPPER_CALL = '})(typeof globalThis!=="undefined"?globalThis:this,'

RECOVER_OLD = "async function recover(q,knownMeta,deadline){if([\"movie\",\"tv\",\"anime\"].indexOf(q.mediaType)<0||Date.now()>=deadline)return[];"
RECOVER_V1 = "async function recover(q,knownMeta,deadline){var nativeRuntime=nativeRecoveryHost(),searchCap=nativeRuntime?2:2147483647,candidateCap=nativeRuntime?2:c.maxCandidates;if([\"movie\",\"tv\",\"anime\"].indexOf(q.mediaType)<0||Date.now()>=deadline)return[];"
RECOVER_NEW = "async function recover(q,knownMeta,deadline){var nativeRuntime=nativeRecoveryHost(),searchCap=nativeRuntime?4:2147483647,candidateCap=nativeRuntime?3:c.maxCandidates;if([\"movie\",\"tv\",\"anime\"].indexOf(q.mediaType)<0||Date.now()>=deadline)return[];"
SEARCH_OLD = "for(var i=0;i<searches.length&&found.length<c.maxCandidates*4&&Date.now()<deadline;i++){"
SEARCH_V1 = "for(var i=0;i<searches.length&&i<searchCap&&found.length<c.maxCandidates*4&&Date.now()<deadline;i++){"
SEARCH_NEW = "if(nativeRuntime)searches=nativeRecoverySearchPlan(searches,searchCap);for(var i=0;i<searches.length&&i<searchCap&&found.length<c.maxCandidates*4&&Date.now()<deadline;i++){"
CANDIDATE_OLD = "var candidates=unique(found.concat(guessed)).slice(0,c.maxCandidates);"
CANDIDATE_V1 = "var candidates=unique(found.concat(guessed)).slice(0,candidateCap);"
CANDIDATE_NEW = "var candidates=nativeRuntime?nativeRecoveryCandidatePlan(found,guessed,candidateCap):unique(found.concat(guessed)).slice(0,candidateCap);"
INSTALL_OLD = "var wrap=async function(){var q=args(arguments),v,deadline=Date.now()+c.budgetMs;"
INSTALL_V1 = "var wrap=async function(){var q=args(arguments),v,deadline=Date.now()+(nativeRecoveryHost()?Math.min(c.budgetMs,12000):c.budgetMs);"
INSTALL_NEW = "var wrap=async function(){var q=args(arguments),v,deadline=Date.now()+(nativeRecoveryHost()?Math.min(c.budgetMs,30000):c.budgetMs);"
HELPER_ANCHOR = 'var TMDB_KEY="8265bd1679663a7ea12ac168da84d2e8";'
HOST_HELPER = 'function nativeRecoveryHost(){try{return typeof g.__native_fetch==="function"}catch(_){return false}}'
HELPER_V1 = HELPER_ANCHOR + HOST_HELPER
SEARCH_PLAN_HELPER = 'function nativeRecoverySearchPlan(values,cap){var out=[],routes=3,aliases=Math.max(1,Math.ceil((values||[]).length/routes)),step=0,max=Math.max((values||[]).length*2,cap*routes);while(out.length<cap&&step<max){var alias=step%aliases,route=Math.floor(step/aliases)%routes,idx=alias*routes+route,u=values[idx];if(u&&out.indexOf(u)<0)out.push(u);step++}return out}'
CANDIDATE_PLAN_HELPER = 'function nativeRecoveryCandidatePlan(found,guessed,cap){var out=[],f=unique(found||[]),g2=unique(guessed||[]),i=0;while(out.length<cap&&(i<f.length||i<g2.length)){if(i<f.length&&out.indexOf(f[i])<0)out.push(f[i]);if(out.length>=cap)break;if(i<g2.length&&out.indexOf(g2[i])<0)out.push(g2[i]);i++}return out.slice(0,cap)}'
HELPER = HELPER_ANCHOR + HOST_HELPER + SEARCH_PLAN_HELPER + CANDIDATE_PLAN_HELPER


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"expected one {label} in global catalogue recovery, found {count}")
    return text.replace(old, new, 1)


def _wrapper_bounds(text: str) -> tuple[int, int]:
    start = text.find(f"/* {CATALOGUE_MARKER}:")
    if start < 0:
        raise ValueError("catalogue recovery marker exists but canonical wrapper marker was not found")
    call = text.find(WRAPPER_CALL, start)
    if call < 0:
        raise ValueError("global catalogue recovery wrapper call not found")
    end = text.find(");", call + len(WRAPPER_CALL))
    if end < 0:
        raise ValueError("global catalogue recovery wrapper end not found")
    return start, end + 2


def _remove_marker(text: str, marker: str) -> str:
    return text.replace(f"\n/* {marker} */\n", "\n").replace(f"/* {marker} */", "")


def _migrate_v1_wrapper(wrapper: str) -> str:
    """Return an old V1-budget wrapper to canonical recovery before installing V2."""
    if HELPER_V1 in wrapper:
        wrapper = _replace_once(wrapper, HELPER_V1, HELPER_ANCHOR, "legacy native helper")
    if RECOVER_V1 in wrapper:
        wrapper = _replace_once(wrapper, RECOVER_V1, RECOVER_OLD, "legacy recover function")
    if SEARCH_V1 in wrapper:
        wrapper = _replace_once(wrapper, SEARCH_V1, SEARCH_OLD, "legacy catalogue search loop")
    if CANDIDATE_V1 in wrapper:
        wrapper = _replace_once(wrapper, CANDIDATE_V1, CANDIDATE_OLD, "legacy candidate slice")
    if INSTALL_V1 in wrapper:
        wrapper = _replace_once(wrapper, INSTALL_V1, INSTALL_OLD, "legacy catalogue wrapper deadline")
    return wrapper


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    if CATALOGUE_MARKER not in text or MARKER in text:
        return text

    had_v1 = LEGACY_MARKER in text
    text = _remove_marker(text, LEGACY_MARKER)
    start, end = _wrapper_bounds(text)
    wrapper = text[start:end]
    if had_v1:
        wrapper = _migrate_v1_wrapper(wrapper)

    wrapper = _replace_once(wrapper, HELPER_ANCHOR, HELPER, "native helper anchor")
    wrapper = _replace_once(wrapper, RECOVER_OLD, RECOVER_NEW, "recover function")
    wrapper = _replace_once(wrapper, SEARCH_OLD, SEARCH_NEW, "catalogue search loop")
    wrapper = _replace_once(wrapper, CANDIDATE_OLD, CANDIDATE_NEW, "candidate slice")
    wrapper = _replace_once(wrapper, INSTALL_OLD, INSTALL_NEW, "catalogue wrapper deadline")
    out = text[:start] + wrapper + text[end:]
    return out.rstrip() + f"\n/* {MARKER} */\n"
