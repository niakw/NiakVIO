#!/usr/bin/env python3
"""Normalize the Terser-compact V5 target resolver before strict target ordering.

The canonical V5 resolver is occasionally already final-Terser normalized when a
published bundle is reconstructed. That compact form is semantically identical but
uses shorthand object properties and removes redundant parentheses, so the strict V1
byte anchor cannot recognize it. This compatibility layer recognizes only that exact
known V5 semantic shape, installs the same ordering contract, and leaves every other
shape untouched for V1 to validate/fail closed.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

BASE_PATH = Path(__file__).with_name("native_sync_fetch_target_order_v1.py")
spec = importlib.util.spec_from_file_location("native_sync_fetch_target_order_v1_minified_base", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot import native_sync_fetch_target_order_v1.py")
BASE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(BASE)

MINIFIED_CONTEXT_RESOLVE = r'''async function resolve(u,baseHeaders,referer,depth,seen,jar){if(depth>c.maxDepth||rejected(u))return[];seen=seen||{};jar=jar||[];if(seen[u])return[];seen[u]=1;var r=await resource(u,baseHeaders,referer,jar);if(!r)return[];var kind=proof(r);if(kind)return[{url:r.url||u,kind,headers:r.headers}];var type=s(r.type).toLowerCase(),body=r.text||"";if(!body||!/text|html|json|javascript|xml/i.test(type)&&!/[<>{}\[\]"']/.test(body))return[];var next=genericUrls(body,r.url||u),groups=await Promise.all(next.map(function(v){return resolve(v,r.headers,r.url||u,depth+1,seen,jar)})),out=[];groups.forEach(function(group){out=out.concat(group)});return unique(out)}'''


def apply(source: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    del options
    if BASE.MARKER in source or BASE.TARGET_MARKER not in source:
        return source
    # Only the playback-context V5 family is eligible. Canonical/unminified V5
    # belongs to the strict V1 transformer and must pass through untouched.
    if "NUVIO_TV_TARGET_MEDIA_V5_PLAYBACK_CONTEXT" not in source:
        return source

    rows_count = source.count(BASE.CONTEXT_TV_ROWS)
    canonical_resolve_count = source.count(BASE.CONTEXT_RESOLVE)
    if canonical_resolve_count == 1 and rows_count == 1:
        return source

    resolve_count = source.count(MINIFIED_CONTEXT_RESOLVE)
    if resolve_count == 0:
        # This compatibility layer owns only the exact un-ordered compact V5
        # resolver above. A later reconstruction can already contain the ordered
        # V1 contract after Terser has compacted it, while still retaining a
        # recognizable V5 tvRows shape. Do not turn that into a false ambiguity:
        # leave it untouched so native_sync_fetch_target_order_v1.py remains the
        # strict final authority (_already_ordered or fail-closed unknown shape).
        return source
    if resolve_count != 1 or rows_count != 1:
        # A canonical V5 shape that the strict V1 patch recognizes (including a
        # source embedded among unrelated provider wrappers) is not a compact-form
        # ambiguity. Everything else remains fail-closed.
        if canonical_resolve_count == 1:
            return source
        raise RuntimeError(
            "Terser V5 target-order compatibility shape is ambiguous: "
            f"resolve={resolve_count} canonicalResolve={canonical_resolve_count} tvRows={rows_count}"
        )
    patched = source.replace(
        MINIFIED_CONTEXT_RESOLVE,
        BASE.HELPERS + "\n" + BASE.CONTEXT_NEW_RESOLVE,
        1,
    )
    patched = patched.replace(BASE.CONTEXT_TV_ROWS, BASE.CONTEXT_NEW_TV_ROWS, 1)
    return patched.rstrip() + f"\n/* {BASE.MARKER} */\n"
