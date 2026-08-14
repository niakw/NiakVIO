#!/usr/bin/env python3
"""Make HLS runtime-integrity capability-aware on native QuickJS clients.

Official Nuvio native runtimes expose a synchronous __native_fetch host bridge. The
HLS integrity wrapper's AbortController timer cannot reliably interrupt an HTTP call
already executing in that bridge, so its validation/recovery probes can stall the
provider for tens of seconds before the final safety layer is reached.

On native Desktop, Mobile Android and Android TV this patch skips *additional*
HLS-integrity network probes. The provider's own resolution still runs, and the final
runtime-capability safety layer still performs deterministic URL rejection.
Non-native/web-like runtimes retain the full HLS validation/recovery path.
"""
from __future__ import annotations

from typing import Any

MARKER = "NUVIO_NATIVE_HLS_INTEGRITY_BUDGET_V1"
HLS_MARKER = "NUVIO_HLS_RUNTIME_INTEGRITY_V1"
USE_STRICT = '  "use strict";'
USE_NATIVE = USE_STRICT + '\n  function nativeHlsHost(){try{return typeof g.__native_fetch==="function"}catch(_e){return false}}'
FILTER_OLD = "  async function filterRows(value){\n    var rows=Array.isArray(value)?value:value&&Array.isArray(value.streams)?value.streams:null;"
FILTER_NEW = "  async function filterRows(value){\n    if(nativeHlsHost())return value;\n    var rows=Array.isArray(value)?value:value&&Array.isArray(value.streams)?value.streams:null;"


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"expected one {label} in HLS runtime integrity wrapper, found {count}")
    return text.replace(old, new, 1)


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    if HLS_MARKER not in text or MARKER in text:
        return text
    out = _replace_once(text, USE_STRICT, USE_NATIVE, "strict-mode anchor")
    out = _replace_once(out, FILTER_OLD, FILTER_NEW, "filterRows entry")
    return out.rstrip() + f"\n/* {MARKER} */\n"
