#!/usr/bin/env python3
"""Transactional BEGIN/END ownership for NiakVIO JavaScript fix blocks.

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
    return f"/* {_PREFIX}_BEGIN:{_fix_id(fix_id)} */"


def end_marker(fix_id: str) -> str:
    return f"/* {_PREFIX}_END:{_fix_id(fix_id)} */"


def data_marker(fix_id: str, data: dict[str, Any] | None) -> str:
    payload = json.dumps(data or {}, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    encoded = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")
    return f"/* {_PREFIX}_DATA:{_fix_id(fix_id)}:{encoded} */"


def _owned_span(text: str, fix_id: str) -> tuple[int, int] | None:
    begin = begin_marker(fix_id)
    end = end_marker(fix_id)
    starts = [match.start() for match in re.finditer(re.escape(begin), text)]
    ends = [match.start() for match in re.finditer(re.escape(end), text)]
    if not starts and not ends:
        return None
    if len(starts) != 1 or len(ends) != 1:
        raise ValueError(
            f"managed fix {fix_id} marker cardinality invalid: "
            f"begin={len(starts)} end={len(ends)}"
        )
    if starts[0] >= ends[0]:
        raise ValueError(f"managed fix {fix_id} END precedes BEGIN")
    nested_begin = text.find("/* NIAKVIO_FIX_BEGIN:", starts[0] + len(begin), ends[0])
    nested_end = text.find("/* NIAKVIO_FIX_END:", starts[0] + len(begin), ends[0])
    if nested_begin >= 0 or nested_end >= 0:
        raise ValueError(f"managed fix {fix_id} contains nested managed markers")
    return starts[0], ends[0] + len(end)


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
    if begin_marker(fix_id) in body or end_marker(fix_id) in body:
        raise ValueError(f"managed fix {fix_id} body contains ownership marker")
    return "\n".join(
        (
            begin_marker(fix_id),
            data_marker(fix_id, data),
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
    base = strip_managed_fix(str(text or ""), fix_id).rstrip()
    block = render_managed_fix(fix_id, javascript, data=data)
    output = (base + "\n" + block).lstrip() if base else block
    assert_single_managed_fix(output, fix_id)
    return output.rstrip() + "\n"


def assert_single_managed_fix(text: str, fix_id: str) -> None:
    span = _owned_span(text, fix_id)
    if span is None:
        raise ValueError(f"managed fix {fix_id} missing after application")
    block = text[span[0] : span[1]]
    data_prefix = f"/* {_PREFIX}_DATA:{_fix_id(fix_id)}:"
    if block.count(data_prefix) != 1:
        raise ValueError(f"managed fix {fix_id} must contain exactly one data marker")


def decode_managed_data(text: str, fix_id: str) -> dict[str, Any]:
    span = _owned_span(text, fix_id)
    if span is None:
        raise ValueError(f"managed fix {fix_id} missing")
    block = text[span[0] : span[1]]
    pattern = re.compile(
        re.escape(f"/* {_PREFIX}_DATA:{_fix_id(fix_id)}:")
        + r"([A-Za-z0-9_=-]+)"
        + re.escape(" */")
    )
    matches = pattern.findall(block)
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
