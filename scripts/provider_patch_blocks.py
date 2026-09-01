#!/usr/bin/env python3
"""Transactional START/END ownership for NiakVIO JavaScript fix blocks.

Every managed fix owns exactly one contiguous block in a published provider
bundle. Reapplying a fix replaces that whole block; it never searches/replaces
fragments inside its previous implementation.

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
_FIX_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9_.:-]{2,95}$")


def _fix_id(value: str) -> str:
    fix_id = str(value or "").strip().upper()
    if not _FIX_ID_RE.fullmatch(fix_id):
        raise ValueError(f"invalid managed fix id: {value!r}")
    return fix_id


def begin_marker(fix_id: str) -> str:
    return f"/* START {_PREFIX}:{_fix_id(fix_id)} */"


def end_marker(fix_id: str) -> str:
    return f"/* END {_PREFIX}:{_fix_id(fix_id)} */"


def legacy_begin_marker(fix_id: str) -> str:
    return f"/* {_PREFIX}_BEGIN:{_fix_id(fix_id)} */"


def legacy_end_marker(fix_id: str) -> str:
    return f"/* {_PREFIX}_END:{_fix_id(fix_id)} */"


def data_markers(fix_id: str, data: dict[str, Any] | None) -> tuple[str, str, str]:
    payload = json.dumps(data or {}, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    encoded = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")
    fid = _fix_id(fix_id)
    return (
        f"/* START {_PREFIX}_DATA:{fid} */",
        f"/* {_PREFIX}_DATA_PAYLOAD:{fid}:{encoded} */",
        f"/* END {_PREFIX}_DATA:{fid} */",
    )


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
    if "/* START NIAKVIO_FIX:" in inner or "/* END NIAKVIO_FIX:" in inner:
        raise ValueError(f"managed fix {fix_id} contains nested managed markers")
    return starts[0], ends[0] + len(end)


def _owned_span(text: str, fix_id: str) -> tuple[int, int] | None:
    current = _span_for_markers(text, fix_id, begin_marker(fix_id), end_marker(fix_id))
    legacy = _span_for_markers(text, fix_id, legacy_begin_marker(fix_id), legacy_end_marker(fix_id))
    if current and legacy:
        raise ValueError(f"managed fix {fix_id} has both current and legacy ownership blocks")
    return current or legacy


def strip_managed_fix(text: str, fix_id: str) -> str:
    span = _owned_span(text, fix_id)
    if span is None:
        return text
    before = text[: span[0]].rstrip()
    after = text[span[1] :].lstrip()
    if before and after:
        return before + "\n" + after
    return before or after


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
    if (
        begin_marker(fix_id) in body
        or end_marker(fix_id) in body
        or legacy_begin_marker(fix_id) in body
        or legacy_end_marker(fix_id) in body
    ):
        raise ValueError(f"managed fix {fix_id} body contains ownership marker")
    data_start, data_payload, data_end = data_markers(fix_id, data)
    return "\n".join(
        (
            begin_marker(fix_id),
            data_start,
            data_payload,
            data_end,
            body,
            end_marker(fix_id),
        )
    )


def replace_managed_fix(
    text: str,
    fix_id: str,
    javascript: str,
    *,
    data: dict[str, Any] | None = None,
) -> str:
    """Replace an owned brick in place; append only on its first materialization."""
    source = str(text or "")
    span = _owned_span(source, fix_id)
    block = render_managed_fix(fix_id, javascript, data=data)
    if span is not None:
        output = source[:span[0]] + block + source[span[1]:]
        assert_single_managed_fix(output, fix_id)
        return output

    base = source.rstrip()
    output = (base + "\n" + block).lstrip() if base else block
    assert_single_managed_fix(output, fix_id)
    return output.rstrip() + "\n"


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
    block = render_managed_fix(fix_id, javascript, data=data)
    output = text[:span[0]] + block + text[span[1]:]
    assert_single_managed_fix(output, fix_id)
    return output, True


def assert_single_managed_fix(text: str, fix_id: str) -> None:
    span = _owned_span(text, fix_id)
    if span is None:
        raise ValueError(f"managed fix {fix_id} missing after application")
    block = text[span[0] : span[1]]
    fid = _fix_id(fix_id)
    current_data = (
        block.count(f"/* START {_PREFIX}_DATA:{fid} */"),
        block.count(f"/* {_PREFIX}_DATA_PAYLOAD:{fid}:"),
        block.count(f"/* END {_PREFIX}_DATA:{fid} */"),
    )
    legacy_data_count = block.count(f"/* {_PREFIX}_DATA:{fid}:")
    if current_data == (1, 1, 1):
        return
    if legacy_data_count == 1:
        return
    raise ValueError(
        f"managed fix {fix_id} data block invalid: "
        f"start={current_data[0]} payload={current_data[1]} end={current_data[2]} "
        f"legacy={legacy_data_count}"
    )


def decode_managed_data(text: str, fix_id: str) -> dict[str, Any]:
    span = _owned_span(text, fix_id)
    if span is None:
        raise ValueError(f"managed fix {fix_id} missing")
    block = text[span[0] : span[1]]
    fid = _fix_id(fix_id)
    current_pattern = re.compile(
        re.escape(f"/* {_PREFIX}_DATA_PAYLOAD:{fid}:")
        + r"([A-Za-z0-9_=-]+)"
        + re.escape(" */")
    )
    legacy_pattern = re.compile(
        re.escape(f"/* {_PREFIX}_DATA:{fid}:")
        + r"([A-Za-z0-9_=-]+)"
        + re.escape(" */")
    )
    matches = current_pattern.findall(block) or legacy_pattern.findall(block)
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
    """Return every managed fix id after proving global marker consistency."""
    source = str(text or "")
    patterns = (
        re.compile(r"/\* START NIAKVIO_FIX:([A-Z0-9_.:-]+) \*/"),
        re.compile(r"/\* END NIAKVIO_FIX:([A-Z0-9_.:-]+) \*/"),
        re.compile(r"/\* NIAKVIO_FIX_BEGIN:([A-Z0-9_.:-]+) \*/"),
        re.compile(r"/\* NIAKVIO_FIX_END:([A-Z0-9_.:-]+) \*/"),
    )
    seen: set[str] = set()
    for pattern in patterns:
        for value in pattern.findall(source):
            seen.add(_fix_id(value))

    for fix_id in sorted(seen):
        assert_single_managed_fix(source, fix_id)
        decode_managed_data(source, fix_id)

    ownership_markers = re.findall(
        r"/\*\s*(?:(?:START|END)\s+NIAKVIO_FIX:[^*]+|NIAKVIO_FIX_(?:BEGIN|END):[^*]+)\*/",
        source,
    )
    if len(ownership_markers) != 2 * len(seen):
        raise ValueError(
            f"malformed managed fix ownership marker(s): "
            f"expected={2 * len(seen)} raw={len(ownership_markers)}"
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
