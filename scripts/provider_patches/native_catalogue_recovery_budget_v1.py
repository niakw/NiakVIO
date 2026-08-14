#!/usr/bin/env python3
"""Bound global catalogue fallback work on native QuickJS clients.

The global catalogue fallback historically relied on AbortSignal + a 45s wall-clock
budget. In official Nuvio native runtimes (Desktop, Mobile Android and Android TV),
__native_fetch is a synchronous host call, so JS AbortSignal cannot reliably interrupt
an in-flight HTTP request. A loop of 8 aliases x 3 search routes can therefore block
for tens of seconds.

This patch is provider-agnostic and only rewrites the already-injected global
catalogue alias recovery wrapper. Non-native/web-like runtimes retain broad recovery;
native runtimes get a small request-count budget instead of a fictitious JS deadline.
"""
from __future__ import annotations

from typing import Any

MARKER = "NUVIO_NATIVE_CATALOGUE_RECOVERY_BUDGET_V1"
CATALOGUE_MARKER = "NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2"

RECOVER_OLD = "async function recover(q,knownMeta,deadline){if([\"movie\",\"tv\",\"anime\"].indexOf(q.mediaType)<0||Date.now()>=deadline)return[];"
RECOVER_NEW = "async function recover(q,knownMeta,deadline){var nativeRuntime=nativeRecoveryHost(),searchCap=nativeRuntime?2:2147483647,candidateCap=nativeRuntime?2:c.maxCandidates;if([\"movie\",\"tv\",\"anime\"].indexOf(q.mediaType)<0||Date.now()>=deadline)return[];"
SEARCH_OLD = "for(var i=0;i<searches.length&&found.length<c.maxCandidates*4&&Date.now()<deadline;i++){"
SEARCH_NEW = "for(var i=0;i<searches.length&&i<searchCap&&found.length<c.maxCandidates*4&&Date.now()<deadline;i++){"
CANDIDATE_OLD = "var candidates=unique(found.concat(guessed)).slice(0,c.maxCandidates);"
CANDIDATE_NEW = "var candidates=unique(found.concat(guessed)).slice(0,candidateCap);"
INSTALL_OLD = "var wrap=async function(){var q=args(arguments),v,deadline=Date.now()+c.budgetMs;"
INSTALL_NEW = "var wrap=async function(){var q=args(arguments),v,deadline=Date.now()+(nativeRecoveryHost()?Math.min(c.budgetMs,12000):c.budgetMs);"
HELPER_ANCHOR = 'var TMDB_KEY="8265bd1679663a7ea12ac168da84d2e8";'
HELPER = HELPER_ANCHOR + 'function nativeRecoveryHost(){try{return typeof g.__native_fetch==="function"}catch(_){return false}}'


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"expected one {label} in global catalogue recovery, found {count}")
    return text.replace(old, new, 1)


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    if CATALOGUE_MARKER not in text or MARKER in text:
        return text
    out = _replace_once(text, HELPER_ANCHOR, HELPER, "native helper anchor")
    out = _replace_once(out, RECOVER_OLD, RECOVER_NEW, "recover function")
    out = _replace_once(out, SEARCH_OLD, SEARCH_NEW, "catalogue search loop")
    out = _replace_once(out, CANDIDATE_OLD, CANDIDATE_NEW, "candidate slice")
    out = _replace_once(out, INSTALL_OLD, INSTALL_NEW, "catalogue wrapper deadline")
    return out.rstrip() + f"\n/* {MARKER} */\n"
