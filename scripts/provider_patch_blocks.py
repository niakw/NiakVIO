#!/usr/bin/env python3
"""Transactional STARTFIX/CLOSEFIX ownership for NiakVIO JavaScript fix blocks.

Every managed fix owns exactly one contiguous STARTFIX/CLOSEFIX block in a published provider
bundle. In clean v3 the owned rectangle includes the line terminator immediately
following CLOSEFIX when one is present. Reapplying or deleting a fix therefore
round-trips the surrounding provider bytes exactly; it never trims neighbors or
searches/replaces fragments inside its previous implementation.

Provider-specific configuration is rendered before the JavaScript body and
recorded as a deterministic base64 JSON data marker. Malformed, nested or
duplicated ownership markers fail closed.
"""
from __future__ import annotations

import base64
import json
import re
from typing import Any

_PREFIX = "NIAKVIO_FIX"
_CURRENT_START_PREFIX = "STARTFIX"
_CURRENT_CLOSE_PREFIX = "CLOSEFIX"
_FIX_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9_.:-]{2,95}$")
PROVIDER_BEGIN_MARKER = "/* BEGIN NIAKVIO_PROVIDER */"
PROVIDER_END_MARKER = "/* END NIAKVIO_PROVIDER */"

def _is_clean_v3_provider(text: str) -> bool:
    source = str(text or "")
    return (
        "NIAKVIO_PROVIDER_BASE_OWNED_V3" in source
        and source.count(PROVIDER_BEGIN_MARKER) == 1
        and source.count(PROVIDER_END_MARKER) == 1
    )



def _fix_id(value: str) -> str:
    fix_id = str(value or "").strip().upper()
    if not _FIX_ID_RE.fullmatch(fix_id):
        raise ValueError(f"invalid managed fix id: {value!r}")
    return fix_id


def begin_marker(fix_id: str) -> str:
    return f"/* {_CURRENT_START_PREFIX}:{_fix_id(fix_id)} */"


def end_marker(fix_id: str) -> str:
    return f"/* {_CURRENT_CLOSE_PREFIX}:{_fix_id(fix_id)} */"


def legacy_begin_marker(fix_id: str) -> str:
    return f"/* START {_PREFIX}:{_fix_id(fix_id)} */"


def legacy_end_marker(fix_id: str) -> str:
    return f"/* END {_PREFIX}:{_fix_id(fix_id)} */"


def legacy_v1_begin_marker(fix_id: str) -> str:
    return f"/* {_PREFIX}_BEGIN:{_fix_id(fix_id)} */"


def legacy_v1_end_marker(fix_id: str) -> str:
    return f"/* {_PREFIX}_END:{_fix_id(fix_id)} */"


def data_marker(fix_id: str, data: dict[str, Any] | None) -> str:
    payload = json.dumps(data or {}, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    encoded = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")
    return f"/* FIXDATA:{_fix_id(fix_id)}:{encoded} */"


def _span_for_markers(text: str, fix_id: str, begin: str, end: str) -> tuple[int, int] | None:
    starts = [match.start() for match in re.finditer(re.escape(begin), text)]
    ends = [match.start() for match in re.finditer(re.escape(end), text)]
    if not starts and not ends:
        return None
    if len(starts) != 1 or len(ends) != 1:
        raise ValueError(
            f"managed fix {fix_id} marker cardinality invalid: "
            f"start={len(starts)} end={len(ends)}"
        )
    if starts[0] >= ends[0]:
        raise ValueError(f"managed fix {fix_id} END precedes START")
    inner = text[starts[0] + len(begin):ends[0]]
    if (
        "/* STARTFIX:" in inner
        or "/* CLOSEFIX:" in inner
        or "/* START NIAKVIO_FIX:" in inner
        or "/* END NIAKVIO_FIX:" in inner
        or "/* NIAKVIO_FIX_BEGIN:" in inner
        or "/* NIAKVIO_FIX_END:" in inner
        or "/* STARTFIXDATA:" in inner
        or "/* CLOSEFIXDATA:" in inner
    ):
        raise ValueError(f"managed fix {fix_id} contains nested managed markers")
    owned_end = ends[0] + len(end)
    if begin.startswith("/* STARTFIX:") and _is_clean_v3_provider(text):
        if text.startswith("\r\n", owned_end):
            owned_end += 2
        elif owned_end < len(text) and text[owned_end] in "\r\n":
            owned_end += 1
    return starts[0], owned_end


def _owned_span(text: str, fix_id: str) -> tuple[int, int] | None:
    current = _span_for_markers(text, fix_id, begin_marker(fix_id), end_marker(fix_id))
    legacy = _span_for_markers(text, fix_id, legacy_begin_marker(fix_id), legacy_end_marker(fix_id))
    legacy_v1 = _span_for_markers(text, fix_id, legacy_v1_begin_marker(fix_id), legacy_v1_end_marker(fix_id))
    present = [span for span in (current, legacy, legacy_v1) if span is not None]
    if len(present) > 1:
        raise ValueError(f"managed fix {fix_id} has multiple ownership block syntaxes")
    return present[0] if present else None


def has_managed_fix(text: str, fix_id: str) -> bool:
    """Return True only when exactly one valid owned block already exists."""
    return _owned_span(str(text or ""), fix_id) is not None


def owned_span(text: str, fix_id: str) -> tuple[int, int] | None:
    """Public exact span for one validated managed brick."""
    return _owned_span(str(text or ""), fix_id)


def strip_managed_fix(text: str, fix_id: str) -> str:
    """Delete exactly one owned rectangle; never trim or rewrite neighboring bytes."""
    source = str(text or "")
    span = _owned_span(source, fix_id)
    if span is None:
        return source
    return source[:span[0]] + source[span[1]:]


def strip_legacy_iife(
    text: str,
    marker: str,
    *,
    invocation_anchor: str = '})(typeof globalThis!=="undefined"?globalThis:this',
) -> str:
    """Remove one pre-managed marker-owned IIFE as one indivisible legacy block."""
    positions = [match.start() for match in re.finditer(re.escape(marker), text)]
    if not positions:
        return text
    if len(positions) != 1:
        raise ValueError(f"legacy fix marker duplicated: {marker}")
    start = positions[0]
    call = text.find(invocation_anchor, start)
    if call < 0:
        raise ValueError(f"legacy fix marker has no owned invocation: {marker}")
    end = text.find(");", call + len(invocation_anchor))
    if end < 0:
        raise ValueError(f"legacy fix marker has unterminated invocation: {marker}")
    end += 2
    before = text[:start].rstrip()
    after = text[end:].lstrip()
    if before and after:
        return before + "\n" + after
    return before or after


def render_managed_fix(
    fix_id: str,
    javascript: str,
    *,
    data: dict[str, Any] | None = None,
) -> str:
    fix_id = _fix_id(fix_id)
    body = str(javascript or "").strip()
    if not body:
        raise ValueError(f"managed fix {fix_id} has empty JavaScript body")
    if any(
        marker in body
        for marker in (
            "/* STARTFIX:",
            "/* CLOSEFIX:",
            "/* START NIAKVIO_FIX:",
            "/* END NIAKVIO_FIX:",
            "/* NIAKVIO_FIX_BEGIN:",
            "/* NIAKVIO_FIX_END:",
        )
    ):
        raise ValueError(f"managed fix {fix_id} body contains nested ownership marker")
    return "\n".join(
        (
            begin_marker(fix_id),
            data_marker(fix_id, data),
            body,
            end_marker(fix_id),
        )
    )


def _render_current_owned_fix(
    fix_id: str,
    javascript: str,
    *,
    data: dict[str, Any] | None = None,
) -> str:
    """Render one current v3 rectangle including its owned CLOSEFIX line ending."""
    return render_managed_fix(fix_id, javascript, data=data) + "\n"


def replace_managed_fix(
    text: str,
    fix_id: str,
    javascript: str,
    *,
    data: dict[str, Any] | None = None,
) -> str:
    """Replace one whole Lego block.

    In Provider architecture v3 every managed Lego lives inside the single
    BEGIN/END PROVIDER envelope. PROVIDER.* bricks stay before the Core boundary;
    CORE.* bricks stay after it. No managed brick may escape the provider.
    """
    source = str(text or "")
    fid = _fix_id(fix_id)
    has_provider_envelope = (
        source.count(PROVIDER_BEGIN_MARKER) == 1
        and source.count(PROVIDER_END_MARKER) == 1
    )
    if has_provider_envelope:
        if fid.startswith("PROVIDER."):
            return replace_provider_fix(source, fid, javascript, data=data)
        if fid.startswith("CORE."):
            return replace_core_fix(source, fid, javascript, data=data)
        raise ValueError(f"v3 managed Lego must be PROVIDER.* or CORE.*: {fid}")

    span = _owned_span(source, fid)
    block = (
        _render_current_owned_fix(fid, javascript, data=data)
        if span is not None
        and _is_clean_v3_provider(source)
        and source[span[0]:].startswith(begin_marker(fid))
        else render_managed_fix(fid, javascript, data=data)
    )
    if span is not None:
        output = source[:span[0]] + block + source[span[1]:]
        assert_single_managed_fix(output, fid)
        return output

    base = source.rstrip()
    output = (base + "\n" + block).lstrip() if base else block
    assert_single_managed_fix(output, fid)
    return output.rstrip() + "\n"


def _first_core_fix_start(text: str, begin: int, provider_end: int) -> int:
    starts: list[int] = []
    for fix_id in managed_fix_ids(text):
        if not fix_id.startswith("CORE."):
            continue
        span = _owned_span(text, fix_id)
        if span is not None and begin < span[0] < span[1] <= provider_end:
            starts.append(span[0])
    return min(starts) if starts else provider_end


def replace_provider_fix(
    text: str,
    fix_id: str,
    javascript: str,
    *,
    data: dict[str, Any] | None = None,
) -> str:
    """Own one PROVIDER.* Lego before every CORE.* Lego, inside Provider."""
    source = str(text or "")
    fid = _fix_id(fix_id)
    if not fid.startswith("PROVIDER."):
        raise ValueError(f"provider Lego id must start with PROVIDER.: {fid}")
    if source.count(PROVIDER_BEGIN_MARKER) != 1 or source.count(PROVIDER_END_MARKER) != 1:
        raise ValueError("provider Lego requires exactly one Provider envelope")
    begin = source.index(PROVIDER_BEGIN_MARKER)
    provider_end = source.index(PROVIDER_END_MARKER)
    if provider_end <= begin:
        raise ValueError("Provider envelope is malformed")
    provider_limit = _first_core_fix_start(source, begin, provider_end)
    span = _owned_span(source, fid)
    clean_v3 = _is_clean_v3_provider(source)
    block = (
        _render_current_owned_fix(fid, javascript, data=data)
        if clean_v3
        else render_managed_fix(fid, javascript, data=data)
    )
    if span is not None:
        if not (begin < span[0] < span[1] <= provider_limit):
            raise ValueError(f"provider Lego escaped provider section: {fid}")
        output = source[:span[0]] + block + source[span[1]:]
    else:
        before = source[:provider_limit]
        after = source[provider_limit:]
        if clean_v3:
            if before and not before.endswith(("\n", "\r")):
                raise ValueError(
                    f"provider Lego insertion point is not a line boundary: {fid}"
                )
            output = before + block + after
        else:
            lead = "" if not before or before.endswith(("\n", "\r")) else "\n"
            tail = "" if not after or after.startswith(("\n", "\r")) else "\n"
            output = before + lead + block + tail + after
    assert_single_managed_fix(output, fid)
    return output


def replace_core_fix(
    text: str,
    fix_id: str,
    javascript: str,
    *,
    data: dict[str, Any] | None = None,
) -> str:
    """Own one CORE.* Lego after all PROVIDER.* Lego and before END PROVIDER."""
    source = str(text or "")
    fid = _fix_id(fix_id)
    if not fid.startswith("CORE."):
        raise ValueError(f"Core Lego id must start with CORE.: {fid}")
    if source.count(PROVIDER_BEGIN_MARKER) != 1 or source.count(PROVIDER_END_MARKER) != 1:
        raise ValueError("Core Lego requires exactly one Provider envelope")
    begin = source.index(PROVIDER_BEGIN_MARKER)
    provider_end = source.index(PROVIDER_END_MARKER)
    if provider_end <= begin:
        raise ValueError("Provider envelope is malformed")

    # A CORE Lego is always appended at the end of the generated Lego chain.
    # Reapplication replaces the complete owned block in place.
    span = _owned_span(source, fid)
    clean_v3 = _is_clean_v3_provider(source)
    block = (
        _render_current_owned_fix(fid, javascript, data=data)
        if clean_v3
        else render_managed_fix(fid, javascript, data=data)
    )
    if span is not None:
        if not (begin < span[0] < span[1] <= provider_end):
            raise ValueError(f"Core Lego escaped Provider envelope: {fid}")
        output = source[:span[0]] + block + source[span[1]:]
    else:
        before = source[:provider_end]
        after = source[provider_end:]
        if clean_v3:
            if before and not before.endswith(("\n", "\r")):
                raise ValueError(
                    f"Core Lego insertion point is not a line boundary: {fid}"
                )
            output = before + block + after
        else:
            lead = "" if not before or before.endswith(("\n", "\r")) else "\n"
            tail = "" if not after or after.startswith(("\n", "\r")) else "\n"
            output = before + lead + block + tail + after
    assert_single_managed_fix(output, fid)

    # Once any CORE.* Lego exists, no PROVIDER.* Lego may appear after it.
    out_begin = output.index(PROVIDER_BEGIN_MARKER)
    out_end = output.index(PROVIDER_END_MARKER)
    first_core = _first_core_fix_start(output, out_begin, out_end)
    for owned_id in managed_fix_ids(output):
        if not owned_id.startswith("PROVIDER."):
            continue
        owned = _owned_span(output, owned_id)
        if owned is None or owned[1] > first_core:
            raise ValueError(f"Provider Lego ordered after Core Lego: {owned_id}")
    return output

def replace_managed_fix_in_place(
    text: str,
    fix_id: str,
    javascript: str,
    *,
    data: dict[str, Any] | None = None,
) -> tuple[str, bool]:
    """Replace an existing managed block at the same byte position."""
    span = _owned_span(text, fix_id)
    if span is None:
        return text, False
    fid = _fix_id(fix_id)
    block = (
        _render_current_owned_fix(fid, javascript, data=data)
        if _is_clean_v3_provider(text)
        and text[span[0]:].startswith(begin_marker(fid))
        else render_managed_fix(fid, javascript, data=data)
    )
    output = text[:span[0]] + block + text[span[1]:]
    assert_single_managed_fix(output, fix_id)
    return output, True


def assert_single_managed_fix(text: str, fix_id: str) -> None:
    span = _owned_span(text, fix_id)
    if span is None:
        raise ValueError(f"managed fix {fix_id} missing after application")
    block = text[span[0] : span[1]]
    fid = _fix_id(fix_id)
    current_data_count = block.count(f"/* FIXDATA:{fid}:")
    legacy_data_count = (
        block.count(f"/* {_PREFIX}_DATA:{fid}:")
        + block.count(f"/* {_PREFIX}_DATA_PAYLOAD:{fid}:")
    )
    if current_data_count == 1:
        return
    if legacy_data_count == 1:
        return
    raise ValueError(
        f"managed fix {fix_id} data marker invalid: "
        f"current={current_data_count} legacy={legacy_data_count}"
    )


def decode_managed_data(text: str, fix_id: str) -> dict[str, Any]:
    span = _owned_span(text, fix_id)
    if span is None:
        raise ValueError(f"managed fix {fix_id} missing")
    block = text[span[0] : span[1]]
    fid = _fix_id(fix_id)
    current_pattern = re.compile(
        re.escape(f"/* FIXDATA:{fid}:")
        + r"([A-Za-z0-9_=-]+)"
        + re.escape(" */")
    )
    legacy_payload_pattern = re.compile(
        re.escape(f"/* {_PREFIX}_DATA_PAYLOAD:{fid}:")
        + r"([A-Za-z0-9_=-]+)"
        + re.escape(" */")
    )
    legacy_pattern = re.compile(
        re.escape(f"/* {_PREFIX}_DATA:{fid}:")
        + r"([A-Za-z0-9_=-]+)"
        + re.escape(" */")
    )
    matches = (
        current_pattern.findall(block)
        or legacy_payload_pattern.findall(block)
        or legacy_pattern.findall(block)
    )
    if len(matches) != 1:
        raise ValueError(f"managed fix {fix_id} data marker invalid")
    try:
        decoded = base64.urlsafe_b64decode(matches[0].encode("ascii")).decode("utf-8")
        value = json.loads(decoded)
    except Exception as exc:
        raise ValueError(f"managed fix {fix_id} data payload invalid") from exc
    if not isinstance(value, dict):
        raise ValueError(f"managed fix {fix_id} data payload must be an object")
    return value


def managed_fix_ids(text: str) -> list[str]:
    """Return every fix id after proving exact STARTFIX/CLOSEFIX ownership."""
    source = str(text or "")
    syntax_pairs = (
        (
            re.compile(r"/\* STARTFIX:([A-Z0-9_.:-]+) \*/"),
            re.compile(r"/\* CLOSEFIX:([A-Z0-9_.:-]+) \*/"),
            "current",
        ),
        (
            re.compile(r"/\* START NIAKVIO_FIX:([A-Z0-9_.:-]+) \*/"),
            re.compile(r"/\* END NIAKVIO_FIX:([A-Z0-9_.:-]+) \*/"),
            "legacy",
        ),
        (
            re.compile(r"/\* NIAKVIO_FIX_BEGIN:([A-Z0-9_.:-]+) \*/"),
            re.compile(r"/\* NIAKVIO_FIX_END:([A-Z0-9_.:-]+) \*/"),
            "legacy-v1",
        ),
    )
    seen: set[str] = set()
    raw_markers = 0
    syntax_by_id: dict[str, set[str]] = {}
    for starts, closes, syntax in syntax_pairs:
        start_ids = [_fix_id(value) for value in starts.findall(source)]
        close_ids = [_fix_id(value) for value in closes.findall(source)]
        raw_markers += len(start_ids) + len(close_ids)
        for value in start_ids + close_ids:
            seen.add(value)
            syntax_by_id.setdefault(value, set()).add(syntax)

    for fix_id in sorted(seen):
        syntaxes = syntax_by_id.get(fix_id, set())
        if len(syntaxes) != 1:
            raise ValueError(
                f"managed fix {fix_id} mixes ownership syntaxes: {sorted(syntaxes)}"
            )
        assert_single_managed_fix(source, fix_id)
        decode_managed_data(source, fix_id)

    if raw_markers != 2 * len(seen):
        raise ValueError(
            "malformed managed fix ownership marker(s): "
            f"expected={2 * len(seen)} raw={raw_markers}"
        )
    return sorted(seen)


def validate_managed_fixes(text: str) -> list[str]:
    """Fail closed on duplicate, nested, malformed or undecodable fix blocks."""
    return managed_fix_ids(text)


def strip_all_managed_fixes(
    text: str,
    *,
    restore_replaced_source: bool = True,
    require_provider_base_restore: bool = False,
) -> tuple[str, list[str]]:
    """Remove all managed fixes and optionally restore exact provider-base source."""
    source = str(text or "")
    fix_ids = validate_managed_fixes(source)
    spans: list[tuple[int, int, str, str]] = []

    for fix_id in fix_ids:
        span = _owned_span(source, fix_id)
        if span is None:
            continue
        data = decode_managed_data(source, fix_id)
        restore = data.get("restore_source", "") if restore_replaced_source else ""
        if restore is None:
            restore = ""
        if not isinstance(restore, str):
            raise ValueError(f"managed fix {fix_id} restore_source must be a string")
        if restore and require_provider_base_restore:
            restore_kind = str(data.get("restore_source_kind") or "").strip()
            if restore_kind != "provider_base":
                raise ValueError(
                    f"managed fix {fix_id} cannot seed ProviderBase from "
                    f"restore_source_kind={restore_kind}"
                )
        spans.append((span[0], span[1], fix_id, restore))

    output = source
    for span_start, span_end, _fix_id_value, restore in sorted(spans, reverse=True):
        output = output[:span_start] + restore + output[span_end:]
    return output, fix_ids
