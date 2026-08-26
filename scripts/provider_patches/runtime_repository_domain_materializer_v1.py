#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Materialize repository-backed runtime domain registries into provider bytes.

Published providers must not fetch GitHub repositories at playback time merely to
resolve a mutable site/API hostname. The maintenance plane resolves and reviews
those values; this patch replaces the provider's named registry resolver with a
static reviewed value and removes configured repository URL literals.
"""
from __future__ import annotations

import json
import re
from typing import Any

MARKER = "NUVIO_RUNTIME_REPOSITORY_DOMAIN_MATERIALIZER_V1"


def _replace_named_function(text: str, function_name: str, replacement: str) -> tuple[str, bool]:
    match = re.search(rf"function\s+{re.escape(function_name)}\s*\([^)]*\)\s*\{{", text)
    if not match:
        return text, False
    start = match.start()
    brace = text.find("{", match.start(), match.end())
    depth = 0
    quote: str | None = None
    escaped = False
    line_comment = False
    block_comment = False
    index = brace
    while index < len(text):
        char = text[index]
        nxt = text[index + 1] if index + 1 < len(text) else ""
        if line_comment:
            if char in "\r\n":
                line_comment = False
        elif block_comment:
            if char == "*" and nxt == "/":
                block_comment = False
                index += 1
        elif quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        else:
            if char in ("'", '"', "`"):
                quote = char
            elif char == "/" and nxt == "/":
                line_comment = True
                index += 1
            elif char == "/" and nxt == "*":
                block_comment = True
                index += 1
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[:start] + replacement + text[index + 1 :], True
        index += 1
    raise ValueError(f"unterminated function body: {function_name}")


def _normalize_payload(value: Any) -> Any:
    if isinstance(value, str):
        url = value.strip().rstrip("/")
        if not url.startswith(("http://", "https://")):
            raise ValueError(f"invalid materialized runtime domain: {value!r}")
        return url
    if isinstance(value, list):
        if not value:
            raise ValueError("materialized runtime domain list must not be empty")
        return [_normalize_payload(item) for item in value]
    if isinstance(value, dict):
        if not value:
            raise ValueError("materialized runtime domain object must not be empty")
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key).strip()
            if not name:
                raise ValueError("materialized runtime domain key must not be empty")
            normalized[name] = _normalize_payload(item)
        return normalized
    raise ValueError(f"unsupported materialized runtime domain payload: {type(value).__name__}")


def apply(
    text: str,
    *,
    options: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> str:
    options = dict(options or {})
    function_name = str(options.get("resolver_function") or "").strip()
    raw_payload = options.get("materialized_value", options.get("values"))
    forbidden_urls = [str(value) for value in (options.get("forbidden_urls") or []) if str(value).strip()]
    if not function_name:
        raise ValueError("runtime repository domain materializer requires resolver_function")
    if raw_payload is None:
        raise ValueError("runtime repository domain materializer requires materialized_value or values")

    normalized = _normalize_payload(raw_payload)
    payload = json.dumps(normalized, ensure_ascii=True, separators=(",", ":"))
    replacement = (
        f"function {function_name}(){{"
        f"/* {MARKER} */"
        f"return Promise.resolve({payload});"
        "}"
    )
    output, changed = _replace_named_function(text, function_name, replacement)
    if not changed:
        provider_id = str((context or {}).get("provider_id") or "unknown")
        raise ValueError(f"runtime repository resolver not found provider={provider_id} function={function_name}")

    # URL constants may remain after the resolver body is replaced. They are dead
    # after Terser, but remove them now so repository-dependency validation is
    # explicit and cannot depend on optimizer behaviour.
    for url in forbidden_urls:
        output = output.replace(url, "")
    remaining = [url for url in forbidden_urls if url in output]
    if remaining:
        raise ValueError("runtime repository URLs remain after materialization: " + ", ".join(remaining))
    return output
