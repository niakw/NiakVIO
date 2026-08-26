#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Materialize repository-backed runtime domain registries into provider bytes.

Published providers must not fetch GitHub repositories at playback time merely to
resolve a mutable site/API hostname. The maintenance plane resolves and reviews
those values; this patch replaces the provider's named registry resolver with a
static reviewed value and removes configured repository URL literals.

Materialized values may reference ``official_site`` / ``official_api`` through a
``{"$from": ..., "fallback": ...}`` node. Those references are resolved from the
current provider-overrides.json at patch time, so hub/Telegram/search/LKG address
resolution automatically feeds the next provider rebuild without copying the
terminal URL into a second configuration surface.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

MARKER = "NUVIO_RUNTIME_REPOSITORY_DOMAIN_MATERIALIZER_V1"
ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "provider-overrides.json"
_CONTEXT_KEYS = {"$from", "fallback"}


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


def _provider_config(context: dict[str, Any] | None) -> dict[str, Any]:
    provider_id = str((context or {}).get("provider_id") or "").strip().casefold()
    if not provider_id:
        return {}
    value = json.loads(CONFIG.read_text(encoding="utf-8"))
    providers = value.get("provider_patches") or {}
    if not isinstance(providers, dict):
        raise ValueError("provider_patches must be an object")
    row = providers.get(provider_id) or {}
    if not isinstance(row, dict):
        raise ValueError(f"provider_patches.{provider_id} must be an object")
    return row


def _resolve_context_payload(value: Any, context: dict[str, Any] | None) -> Any:
    if isinstance(value, dict) and "$from" in value and set(value).issubset(_CONTEXT_KEYS):
        field = str(value.get("$from") or "").strip()
        if not field:
            raise ValueError("materialized runtime context reference requires $from")
        row = _provider_config(context)
        selected = row.get(field)
        if selected is None or (isinstance(selected, str) and not selected.strip()):
            selected = value.get("fallback")
        if selected is None:
            provider_id = str((context or {}).get("provider_id") or "unknown")
            raise ValueError(
                f"materialized runtime context value missing provider={provider_id} field={field}"
            )
        return selected
    if isinstance(value, list):
        return [_resolve_context_payload(item, context) for item in value]
    if isinstance(value, dict):
        return {str(key): _resolve_context_payload(item, context) for key, item in value.items()}
    return value


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
    mode = str(options.get("mode") or "return").strip().casefold()
    if not function_name:
        raise ValueError("runtime repository domain materializer requires resolver_function")
    if raw_payload is None:
        raise ValueError("runtime repository domain materializer requires materialized_value or values")

    resolved_payload = _resolve_context_payload(raw_payload, context)
    normalized = _normalize_payload(resolved_payload)
    payload = json.dumps(normalized, ensure_ascii=True, separators=(",", ":"))
    if mode == "return":
        body = f"return Promise.resolve({payload});"
    elif mode == "assign":
        target = str(options.get("assign_target") or "").strip()
        if not re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", target):
            raise ValueError("runtime repository assignment mode requires a safe assign_target identifier")
        if not isinstance(normalized, str):
            raise ValueError("runtime repository assignment mode requires a scalar URL payload")
        body = f"{target}={payload};return Promise.resolve();"
    else:
        raise ValueError(f"unsupported runtime repository materializer mode: {mode}")

    replacement = (
        f"function {function_name}(){{"
        f"/* {MARKER} */"
        f"{body}"
        "}"
    )
    output, changed = _replace_named_function(text, function_name, replacement)
    if not changed:
        # A discovery/global-Core fixture, an already-purified provider, or a
        # newer upstream may legitimately no longer expose the historical
        # resolver. Absence is safe only when none of the configured runtime
        # repository registries remains in the bytes. If a registry is still
        # present, fail closed: the provider changed shape and requires review.
        remaining = [url for url in forbidden_urls if url in text]
        if remaining:
            provider_id = str((context or {}).get("provider_id") or "unknown")
            raise ValueError(
                "runtime repository resolver not found while registry dependency remains "
                f"provider={provider_id} function={function_name} urls={','.join(remaining)}"
            )
        return text

    # URL constants may remain after the resolver body is replaced. They are dead
    # after Terser, but remove them now so repository-dependency validation is
    # explicit and cannot depend on optimizer behaviour.
    for url in forbidden_urls:
        output = output.replace(url, "")
    remaining = [url for url in forbidden_urls if url in output]
    if remaining:
        raise ValueError("runtime repository URLs remain after materialization: " + ", ".join(remaining))
    return output