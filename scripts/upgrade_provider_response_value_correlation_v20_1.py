#!/usr/bin/env python3
"""V20.1: compose response-value correlation with the V16 slug proof owner.

V20 originally targeted the pre-V16 provider_route_proof.py shape. The canonical
repair chain installs V16 first, so V20 must preserve V16's semantic placeholder
map instead of replacing an obsolete adjacent helper block.

This migration stays provider-agnostic:
- legacy/pre-V16 trees delegate to V20 unchanged;
- post-V16 trees replace only the two proof helper functions by AST span;
- V16's provider_placeholders remains authoritative for id-vs-slug semantics;
- arbitrary safe response query keys may correlate, while volatile/content keys
  remain fail-closed.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import upgrade_provider_response_value_correlation_v20 as legacy  # noqa: E402

PROOF = legacy.PROOF
MARKER = legacy.MARKER
V16_MARKER = "PROVIDER_ROUTE_PROOF_SLUG_IDENTITY_V16"
COMPAT_MARKER = "NIAKVIO_PROVIDER_RESPONSE_VALUE_CORRELATION_V20_1"


def _function_span(text: str, name: str) -> tuple[int, int]:
    tree = ast.parse(text)
    node = next(
        (
            item
            for item in tree.body
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == name
        ),
        None,
    )
    if node is None or node.end_lineno is None:
        raise AssertionError(f"v20.1 missing function anchor: {name}")
    lines = text.splitlines(keepends=True)
    start = sum(len(line) for line in lines[: node.lineno - 1])
    end = sum(len(line) for line in lines[: node.end_lineno])
    return start, end


def _replace_function(text: str, name: str, source: str) -> str:
    start, end = _function_span(text, name)
    suffix = "\n" if not source.endswith("\n") else ""
    return text[:start] + source + suffix + text[end:]


def _once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_proof() -> bool:
    text = PROOF.read_text(encoding="utf-8")
    if MARKER in text:
        validate_proof(text)
        return False

    # A direct/standalone V20 invocation on the repository baseline still uses
    # the original V20 migration. The canonical repair boundary is post-V16.
    if V16_MARKER not in text:
        changed = legacy.patch_proof()
        validate_proof()
        return changed

    helper_block = '''# NIAKVIO_PROVIDER_RESPONSE_VALUE_CORRELATION_V20\n# NIAKVIO_PROVIDER_RESPONSE_VALUE_CORRELATION_V20_1\n_PROVIDER_HINT_SENSITIVE_KEY = re.compile(\n    r"api[_-]?key|token|auth|authorization|signature|sig|secret|password|cookie|session|nonce",\n    re.I,\n)\n\n\ndef _provider_hint_rows(prior_value_hints: Iterable[dict[str, Any]] | None) -> list[dict[str, str]]:\n    out: list[dict[str, str]] = []\n    seen: set[tuple[str, str]] = set()\n    for row in prior_value_hints or []:\n        if not isinstance(row, dict):\n            continue\n        key = canonical(row.get("key"))\n        value = str(row.get("value") or "").strip()\n        if not key or not value or len(value) < 2 or len(value) > 160:\n            continue\n        if _PROVIDER_HINT_SENSITIVE_KEY.search(key) or key in VOLATILE_QUERY_KEYS:\n            continue\n        if not re.fullmatch(r"[A-Za-z0-9._~-]+", value):\n            continue\n        fp = (key, value)\n        if fp in seen:\n            continue\n        seen.add(fp)\n        out.append({"key": key, "value": value})\n    return out[:160]\n\n\ndef _provider_hint_values_for_keys(\n    prior_value_hints: Iterable[dict[str, Any]] | None,\n    keys: set[str],\n) -> set[str]:\n    wanted = {canonical(value) for value in keys}\n    return {row["value"] for row in _provider_hint_rows(prior_value_hints) if row["key"] in wanted}\n\n\n'''

    provider_values_source = '''def _provider_hint_values(prior_value_hints: Iterable[dict[str, Any]] | None) -> set[str]:\n    return {row["value"] for row in _provider_hint_rows(prior_value_hints)}\n'''
    response_hints_source = '''def response_value_hints(fetch: dict[str, Any]) -> list[dict[str, str]]:\n    rows = fetch.get("response_value_hints")\n    if not isinstance(rows, list):\n        return []\n    return _provider_hint_rows(rows)[:80]\n'''

    start, _ = _function_span(text, "_provider_hint_values")
    text = text[:start] + helper_block + text[start:]
    text = _replace_function(text, "_provider_hint_values", provider_values_source)
    text = _replace_function(text, "response_value_hints", response_hints_source)

    text = _once(
        text,
        '''    provider_values = _provider_hint_values(prior_value_hints)\n    provider_placeholders = _provider_hint_placeholders(prior_value_hints)\n\n    tmdb = str(fixture.get("tmdbId") or "").strip()\n''',
        '''    provider_values = _provider_hint_values(prior_value_hints)\n    provider_slugs = _provider_hint_values_for_keys(prior_value_hints, {"slug"})\n    provider_placeholders = _provider_hint_placeholders(prior_value_hints)\n\n    tmdb = str(fixture.get("tmdbId") or "").strip()\n''',
        "v20.1-route-provider-slugs",
    )
    text = _once(
        text,
        '''        elif decoded in provider_values:\n            placeholder = provider_placeholders.get(decoded, "{id}")\n''',
        '''        elif decoded in provider_slugs:\n            placeholder = "{slug}"\n        elif decoded in provider_values:\n            placeholder = provider_placeholders.get(decoded, "{id}")\n''',
        "v20.1-path-slug-before-id",
    )
    text = _once(
        text,
        '''        elif value in provider_values and key_l in PROVIDER_VALUE_KEYS:\n            placeholder = provider_placeholders.get(value, "{id}")\n''',
        '''        elif value in provider_values and key_l not in VOLATILE_QUERY_KEYS | CONTENT_IDENTITY_QUERY_KEYS:\n            placeholder = "{slug}" if value in provider_slugs else provider_placeholders.get(value, "{id}")\n''',
        "v20.1-query-safe-response-value",
    )

    PROOF.write_text(text, encoding="utf-8")
    validate_proof(text)
    return True


def validate_proof(text: str | None = None) -> None:
    value = text if text is not None else PROOF.read_text(encoding="utf-8")
    legacy.validate_proof(value)
    if V16_MARKER in value:
        for needle in (
            COMPAT_MARKER,
            "provider_placeholders = _provider_hint_placeholders(prior_value_hints)",
            'placeholder = "{slug}" if value in provider_slugs else provider_placeholders.get(value, "{id}")',
        ):
            if needle not in value:
                raise AssertionError(f"V20.1 proof compatibility missing: {needle}")


patch_worker = legacy.patch_worker
patch_recovery = legacy.patch_recovery
patch_materializer = legacy.patch_materializer
patch_base = legacy.patch_base
validate_worker = legacy.validate_worker
validate_recovery = legacy.validate_recovery
validate_materializer = legacy.validate_materializer
validate_base = legacy.validate_base


def main() -> int:
    changed = patch_worker() | patch_proof() | patch_recovery() | patch_materializer() | patch_base()
    validate_worker()
    validate_proof()
    validate_recovery()
    validate_materializer()
    validate_base()
    print(
        f"PROVIDER_RESPONSE_VALUE_CORRELATION_V20_1_OK changed={str(changed).lower()} "
        "v16_composition=1 ast_function_patch=1 safe_query_dataflow=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
