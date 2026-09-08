#!/usr/bin/env python3
"""V20.1: structural response-value correlation after canonical proof migrations.

V20 originally assumed historical text layouts in proof/materialization and used a
single-anchor helper for two intentionally identical ProviderBase value maps. The
current repair chain applies V11/V18 before live census, so this owner composes with
those owners while keeping V20 provider-agnostic.

Invariants:
- safe response values are hints only; exact later request consumption is required;
- auth/session/signature/volatile values remain non-reusable;
- IMDb-shaped external identities remain external identities, never provider ids;
- href/query-derived slugs remain {slug}; other safe correlated values become {id};
- V18 materializers already copying structured steps are left non-destructively open;
- ProviderBase's two intentional recipe value maps are patched deterministically;
- no provider hostname, id, title, selector or route is encoded here.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import upgrade_provider_response_value_correlation_v20 as legacy  # noqa: E402

PROOF = legacy.PROOF
MATERIALIZER = legacy.MATERIALIZER
MARKER = legacy.MARKER
COMPAT_MARKER = "NIAKVIO_PROVIDER_RESPONSE_VALUE_CORRELATION_V20_1"
MATERIALIZER_MARKER = "PROVIDER_RESPONSE_VALUE_CORRELATION_V20"


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


def _function_source(text: str, name: str) -> str:
    start, end = _function_span(text, name)
    return text[start:end]


def _replace_function(text: str, name: str, source: str) -> str:
    start, end = _function_span(text, name)
    if not source.endswith("\n"):
        source += "\n"
    return text[:start] + source + text[end:]


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

    has_external_identity = "def _external_identity_hint_values" in text
    has_semantic_placeholders = "def _provider_hint_placeholders" in text

    helper_block = '''# NIAKVIO_PROVIDER_RESPONSE_VALUE_CORRELATION_V20\n# NIAKVIO_PROVIDER_RESPONSE_VALUE_CORRELATION_V20_1\n_PROVIDER_HINT_SENSITIVE_KEY = re.compile(\n    r"api[_-]?key|token|auth|authorization|signature|sig|secret|password|cookie|session|nonce",\n    re.I,\n)\n\n\ndef _provider_hint_rows(prior_value_hints: Iterable[dict[str, Any]] | None) -> list[dict[str, str]]:\n    out: list[dict[str, str]] = []\n    seen: set[tuple[str, str]] = set()\n    for row in prior_value_hints or []:\n        if not isinstance(row, dict):\n            continue\n        key = canonical(row.get("key"))\n        value = str(row.get("value") or "").strip()\n        if not key or not value or len(value) < 2 or len(value) > 160:\n            continue\n        if _PROVIDER_HINT_SENSITIVE_KEY.search(key) or key in VOLATILE_QUERY_KEYS:\n            continue\n        if not re.fullmatch(r"[A-Za-z0-9._~-]+", value):\n            continue\n        fp = (key, value)\n        if fp in seen:\n            continue\n        seen.add(fp)\n        out.append({"key": key, "value": value})\n    return out[:160]\n\n\ndef _provider_hint_values_for_keys(\n    prior_value_hints: Iterable[dict[str, Any]] | None,\n    keys: set[str],\n) -> set[str]:\n    wanted = {canonical(value) for value in keys}\n    return {row["value"] for row in _provider_hint_rows(prior_value_hints) if row["key"] in wanted}\n\n\n'''
    provider_values_source = '''def _provider_hint_values(prior_value_hints: Iterable[dict[str, Any]] | None) -> set[str]:\n    out: set[str] = set()\n    for row in _provider_hint_rows(prior_value_hints):\n        value = row["value"]\n        # Preserve V11 external IMDb ownership: an IMDb-shaped value is never a\n        # provider-internal id even if an upstream response called the field id.\n        if re.fullmatch(r"tt\\d{7,10}", value, re.I):\n            continue\n        out.add(value)\n    return out\n'''
    response_hints_source = '''def response_value_hints(fetch: dict[str, Any]) -> list[dict[str, str]]:\n    rows = fetch.get("response_value_hints")\n    if not isinstance(rows, list):\n        return []\n    return _provider_hint_rows(rows)[:80]\n'''

    start, _ = _function_span(text, "_provider_hint_values")
    text = text[:start] + helper_block + text[start:]
    text = _replace_function(text, "_provider_hint_values", provider_values_source)
    text = _replace_function(text, "response_value_hints", response_hints_source)

    route_source = _function_source(text, "derive_observed_route")
    route_source = _once(
        route_source,
        "    provider_values = _provider_hint_values(prior_value_hints)\n",
        "    provider_values = _provider_hint_values(prior_value_hints)\n"
        "    provider_slugs = _provider_hint_values_for_keys(prior_value_hints, {\"slug\"})\n",
        "v20.1-route-provider-slugs",
    )

    if has_semantic_placeholders:
        provider_path_old = '''        elif decoded in provider_values:\n            placeholder = provider_placeholders.get(decoded, "{id}")\n'''
        provider_path_new = '''        elif decoded in provider_slugs:\n            placeholder = "{slug}"\n        elif decoded in provider_values:\n            placeholder = provider_placeholders.get(decoded, "{id}")\n'''
        provider_query_old = '''        elif value in provider_values and key_l in PROVIDER_VALUE_KEYS:\n            placeholder = provider_placeholders.get(value, "{id}")\n'''
        provider_query_new = '''        elif value in provider_values and key_l not in VOLATILE_QUERY_KEYS | CONTENT_IDENTITY_QUERY_KEYS:\n            placeholder = "{slug}" if value in provider_slugs else provider_placeholders.get(value, "{id}")\n'''
    else:
        provider_path_old = '''        elif decoded in provider_values:\n            placeholder = "{id}"\n'''
        provider_path_new = '''        elif decoded in provider_slugs:\n            placeholder = "{slug}"\n        elif decoded in provider_values:\n            placeholder = "{id}"\n'''
        provider_query_old = '''        elif value in provider_values and key_l in PROVIDER_VALUE_KEYS:\n            placeholder = "{id}"\n'''
        provider_query_new = '''        elif value in provider_values and key_l not in VOLATILE_QUERY_KEYS | CONTENT_IDENTITY_QUERY_KEYS:\n            placeholder = "{slug}" if value in provider_slugs else "{id}"\n'''

    route_source = _once(route_source, provider_path_old, provider_path_new, "v20.1-path-slug-before-id")
    route_source = _once(route_source, provider_query_old, provider_query_new, "v20.1-query-safe-response-value")

    old_correlation = '        "providerValueCorrelation": bool(provider_values and any(row.get("placeholder") == "{id}" for row in substitutions)),\n'
    if old_correlation in route_source:
        route_source = _once(
            route_source,
            old_correlation,
            '        "providerValueCorrelation": bool(provider_values and any(row.get("placeholder") in {"{id}", "{slug}"} for row in substitutions)),\n',
            "v20.1-correlation-id-or-slug",
        )
    elif 'row.get("placeholder") in {"{id}", "{slug}"}' not in route_source:
        raise AssertionError("v20.1 provider correlation anchor missing")

    text = _replace_function(text, "derive_observed_route", route_source)
    PROOF.write_text(text, encoding="utf-8")
    validate_proof(text)

    if has_external_identity:
        current = PROOF.read_text(encoding="utf-8")
        for needle in ("def _external_identity_hint_values", 'placeholder = "{imdbId}"', '"externalIdentityCorrelation"'):
            if needle not in current:
                raise AssertionError(f"V20.1 lost V11 external identity: {needle}")
    return True


def validate_proof(text: str | None = None) -> None:
    value = text if text is not None else PROOF.read_text(encoding="utf-8")
    for needle in (
        MARKER,
        COMPAT_MARKER,
        "def _provider_hint_rows",
        "def _provider_hint_values_for_keys",
        'provider_slugs = _provider_hint_values_for_keys(prior_value_hints, {"slug"})',
        'placeholder = "{slug}"',
        'key_l not in VOLATILE_QUERY_KEYS | CONTENT_IDENTITY_QUERY_KEYS',
        'row.get("placeholder") in {"{id}", "{slug}"}',
        're.fullmatch(r"tt\\d{7,10}", value, re.I)',
    ):
        if needle not in value:
            raise AssertionError(f"V20.1 proof missing {needle}")


def patch_materializer() -> bool:
    text = MATERIALIZER.read_text(encoding="utf-8")
    if MATERIALIZER_MARKER in text:
        validate_materializer(text)
        return False

    id_only = '                    and "{id}" in str(step.get("route") or "")\n'
    if id_only in text:
        text = _once(
            text,
            id_only,
            '                    # PROVIDER_RESPONSE_VALUE_CORRELATION_V20\n'
            '                    and ("{id}" in str(step.get("route") or "") or "{slug}" in str(step.get("route") or ""))\n',
            "v20.1-materializer-id-or-slug",
        )
    else:
        # Current V18 materialization already copies the proof-owned structured
        # step rows without an id-only filter. Keep that open semantic projection.
        anchor = '        # PROVIDER_CORRELATED_VALUE_PLAN_V18\n        "providerValuePlan": [\n'
        text = _once(
            text,
            anchor,
            '        # PROVIDER_RESPONSE_VALUE_CORRELATION_V20\n' + anchor,
            "v20.1-materializer-unfiltered-v18-plan",
        )

    MATERIALIZER.write_text(text, encoding="utf-8")
    validate_materializer(text)
    return True


def validate_materializer(text: str | None = None) -> None:
    value = text if text is not None else MATERIALIZER.read_text(encoding="utf-8")
    if MATERIALIZER_MARKER not in value:
        raise AssertionError("V20.1 materializer marker missing")
    if '"providerValuePlan": [' not in value:
        raise AssertionError("V20.1 materializer providerValuePlan missing")
    if 'and "{id}" in str(step.get("route") or "")' in value and 'or "{slug}" in str(step.get("route") or "")' not in value:
        raise AssertionError("V20.1 materializer retains an id-only provider-value step filter")


def patch_base() -> bool:
    """Run canonical V20 Base patch with its intentional two-map precondition.

    Legacy V20 calls `once()` twice on the same ProviderBase mapping. Before the
    first call there are exactly two copies by design, so strict count==1 aborts.
    Permit count==2 only for that first labelled operation; after one replacement,
    the second canonical call sees exactly one remaining copy and stays strict.
    """
    original_once = legacy.once

    def compatible_once(text: str, old: str, new: str, label: str) -> str:
        if label == "v20-base-recipe-url-slug":
            count = text.count(old)
            if count != 2:
                raise AssertionError(f"{label}: expected two intentional anchors, got {count}")
            return text.replace(old, new, 1)
        return original_once(text, old, new, label)

    legacy.once = compatible_once
    try:
        return legacy.patch_base()
    finally:
        legacy.once = original_once


patch_worker = legacy.patch_worker
patch_recovery = legacy.patch_recovery
validate_worker = legacy.validate_worker
validate_recovery = legacy.validate_recovery
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
        "structural_proof_patch=1 external_identity_preserved=1 materializer_composed=1 "
        "base_duplicate_maps_composed=1 safe_query_dataflow=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
