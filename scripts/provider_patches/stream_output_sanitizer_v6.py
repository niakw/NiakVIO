#!/usr/bin/env python3
"""Harden V5 all-URL probing and preserve terminal wrapper order.

V5 treats ``maxProbes`` as a probing budget, but rows beyond that budget are
returned unchanged even when ``probe_all_urls`` is true. That is acceptable for
best-effort probing, but not for a strict publication boundary: every published
row must either have media proof or be discarded.

A second subtlety matters on durable/LKG rematerialization. Some target-media
profiles deliberately remove their old wrapper and append a fresh one. If an
already-materialized sanitizer is left in place, the new target-media wrapper is
installed after it and therefore becomes the outer wrapper at runtime. The final
media URL then bypasses the terminal sanitizer entirely. V6 detects that stale
textual order, removes only its own sanitizer wrapper/markers, and lets V5
rebuild it after target-media. This keeps reapplication deterministic without
weakening fail-closed probing or adding provider-specific behavior.

V5 historically detects its compatibility ``probe()`` alias with a whole-file
substring search. A provider or another wrapper may coincidentally define the
same function, causing V5 to skip the alias inside the sanitizer and fail at
runtime with ``ReferenceError: probe is not defined``. V6 verifies the alias in
the sanitizer's own lexical region and injects it there when needed. Detection
is structural rather than formatting-dependent because already-published legacy
bundles may have compact formatting before the next Core reconstruction.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from provider_patch_blocks import has_managed_fix, render_managed_fix, replace_managed_fix, strip_managed_fix
V5_PATH = ROOT / "stream_output_sanitizer_v5.py"
MARKER = "/* NUVIO_STREAM_OUTPUT_SANITIZER_ALL_URL_FAIL_CLOSED_V6 */"
MANAGED_FIX_ID = "CORE.STREAM_SANITIZER.V6"
OLD = "if(!item.probe)return item.stream;"
NEW = "if(!item.probe)return config.probeAllUrls?null:item.stream;"
SANITIZER_PREFIX = "/* NUVIO_STREAM_OUTPUT_SANITIZER_V4:"
SANITIZER_CALL = '})(typeof globalThis!=="undefined"?globalThis:this,'
V5_MARKERS = (
    "/* NUVIO_STREAM_OUTPUT_SANITIZER_UTF8_BOM_V5 */",
    "/* NUVIO_STREAM_OUTPUT_HLS_HTML_REPAIR_V7 */",
)
TARGET_MEDIA_MARKERS = (
    "/* NUVIO_TV_TARGET_MEDIA_V3:",
    "/* NUVIO_TV_TARGET_MEDIA_V4 */",
    "/* NUVIO_TV_TARGET_MEDIA_V5_PLAYBACK_CONTEXT */",
    "/* NUVIO_TV_TARGET_MEDIA_HLS_PROOF_V6 */",
)
CORE_PREDECESSOR_MARKERS = TARGET_MEDIA_MARKERS + (
    "/* NUVIO_GLOBAL_STREAM_PRESENTATION_V1:",
    "/* NUVIO_GLOBAL_PROVIDER_BRANDING_V1:",
)
PROBE_RESOLVED = "  async function probeResolved(stream,url,depth,referer){\n"
PROBE_ALIAS = '  async function probe(stream,url){return await probeResolved(stream,url,0,"")}\n'
INSTALL_ANCHOR = "  function install(container,key){\n"
PROBE_RESOLVED_RE = re.compile(
    r"async\s+function\s+probeResolved\s*\(\s*stream\s*,\s*url\s*,\s*depth\s*,\s*referer\s*\)\s*\{"
)
PROBE_ALIAS_RE = re.compile(
    r"async\s+function\s+probe\s*\(\s*stream\s*,\s*url\s*\)\s*\{\s*"
    r"return\s+await\s+probeResolved\s*\(\s*stream\s*,\s*url\s*,\s*0\s*,\s*[\"']{2}\s*\)\s*;?\s*\}"
)
INSTALL_ANCHOR_RE = re.compile(
    r"function\s+install\s*\(\s*container\s*,\s*key\s*\)\s*\{"
)


def _load_v5_apply():
    spec = importlib.util.spec_from_file_location("stream_output_sanitizer_v5_for_v6", V5_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {V5_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


V5_APPLY = _load_v5_apply()


def _latest_predecessor_position(text: str) -> int:
    """Latest stream-transform layer that must remain inside the sanitizer."""
    return max((text.rfind(marker) for marker in CORE_PREDECESSOR_MARKERS), default=-1)


def _sanitizer_position(text: str) -> int:
    return text.find(SANITIZER_PREFIX)


def _needs_relocation(text: str) -> bool:
    sanitizer = _sanitizer_position(text)
    predecessor = _latest_predecessor_position(text)
    return sanitizer >= 0 and predecessor > sanitizer


def _strip_existing_sanitizer(text: str) -> str:
    """Remove the existing V4/V5/V6 sanitizer materialization only.

    The wrapper boundary is stable because the base sanitizer is emitted as one
    IIFE. Other provider/global wrappers are preserved byte-for-byte.
    """
    output = text
    removed = 0
    while True:
        start = output.find(SANITIZER_PREFIX)
        if start < 0:
            break
        call = output.find(SANITIZER_CALL, start)
        end = output.find(");", call) if call >= 0 else -1
        if call < 0 or end < 0:
            raise ValueError("unterminated stream sanitizer wrapper during relocation")
        output = (output[:start] + output[end + 2 :]).rstrip()
        removed += 1
    if removed == 0:
        raise ValueError("stream sanitizer relocation requested without wrapper")
    for marker in (*V5_MARKERS, MARKER):
        output = output.replace(marker, "")
    return output.rstrip()


def _ensure_local_probe_alias(text: str) -> str:
    """Ensure ``probe()`` exists inside this sanitizer, independent of formatting."""
    sanitizer = _sanitizer_position(text)
    if sanitizer < 0:
        return text
    resolved = PROBE_RESOLVED_RE.search(text, sanitizer)
    if resolved is None:
        raise ValueError("stream sanitizer local probeResolved region not found")
    install = INSTALL_ANCHOR_RE.search(text, resolved.end())
    if install is None:
        raise ValueError("stream sanitizer local install region not found")
    region = text[resolved.start():install.start()]
    if PROBE_ALIAS_RE.search(region):
        return text
    return text[:install.start()] + PROBE_ALIAS + text[install.start():]


def _extract_sanitizer_unit(text: str) -> tuple[str, str]:
    """Split the generated sanitizer IIFE from untouched provider/Core bytes."""
    start = _sanitizer_position(text)
    if start < 0:
        raise ValueError("generated stream sanitizer wrapper not found")
    call = text.find(SANITIZER_CALL, start)
    end = text.find(");", call) if call >= 0 else -1
    if call < 0 or end < 0:
        raise ValueError("unterminated generated stream sanitizer wrapper")
    end += 2
    unit = text[start:end].strip()
    body = (text[:start] + text[end:]).strip()
    for marker in (*V5_MARKERS, MARKER):
        body = body.replace(marker, "")
    body = body.strip()
    if SANITIZER_PREFIX in body:
        raise ValueError("multiple sanitizer wrappers after extraction")
    return body, unit


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    cfg = dict(options or {})
    if not bool(cfg.get("probe_all_urls")):
        raise ValueError("stream sanitizer v6 requires probe_all_urls=true")
    if int(cfg.get("max_probes") or 0) <= 0:
        raise ValueError("stream sanitizer v6 requires max_probes>0")

    # Generate from a source view without the owned sanitizer, while preserving
    # the original bundle so an existing START/END block can be replaced in place.
    owned = has_managed_fix(text, MANAGED_FIX_ID)
    relocate_owned = owned and _needs_relocation(text)
    source = strip_managed_fix(text, MANAGED_FIX_ID) if owned else text
    if not owned and _sanitizer_position(source) >= 0:
        source = _strip_existing_sanitizer(source)

    # V4/V5 are implementation builders only. Their temporary compatibility
    # markers never escape this function into the published Lego bundle.
    patched = V5_APPLY(source, options=cfg, **kwargs)
    patched = _ensure_local_probe_alias(patched)
    patched = patched.replace(MARKER, "").rstrip()

    if NEW not in patched:
        if OLD not in patched:
            raise ValueError("stream sanitizer all-URL overflow hook not found")
        patched = patched.replace(OLD, NEW, 1)

    body, sanitizer_unit = _extract_sanitizer_unit(patched)
    managed_data = {
        "probeAllUrls": True,
        "maxProbes": max(1, int(cfg.get("max_probes") or 1)),
        "probeTimeoutMs": int(cfg.get("probe_timeout_ms") or 6500),
        "minVodDurationSeconds": int(cfg.get("min_vod_duration_seconds") or 60),
        "implementationRevision": "terminal-single-owner-v6",
    }
    if owned and body.rstrip() != source.rstrip():
        raise ValueError("managed sanitizer rebuild mutated bytes outside its owned block")

    if owned and not relocate_owned:
        output = replace_managed_fix(
            text,
            MANAGED_FIX_ID,
            sanitizer_unit,
            data=managed_data,
        )
    else:
        # Initial materialization or one-time repair of a provably stale terminal
        # position. Once appended after all predecessors, subsequent applies are
        # strict in-place replacements.
        managed = render_managed_fix(
            MANAGED_FIX_ID,
            sanitizer_unit,
            data=managed_data,
        )
        output = (body.rstrip() + "\n" if body else "") + managed.strip() + "\n"
    sanitizer = output.find(f"/* START NIAKVIO_FIX:{MANAGED_FIX_ID} */")
    predecessor = _latest_predecessor_position(output)
    if sanitizer < 0 or (predecessor >= 0 and sanitizer <= predecessor):
        raise ValueError(
            f"stream sanitizer terminal order invalid: sanitizer={sanitizer} predecessor={predecessor}"
        )
    return output


if __name__ == "__main__":
    raise SystemExit("patch module; import apply()")
