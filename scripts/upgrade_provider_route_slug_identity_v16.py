#!/usr/bin/env python3
"""Route Proof V16: preserve response-value semantic identity in placeholders.

A value learned from a prior provider response is not always an opaque provider
ID. In particular, response fields named `slug` must remain `{slug}` when reused
in a later path/body/query. Collapsing every prior-response value to `{id}` makes
valid catalogue dataflow impossible to replay when the search row exposes a slug
but no numeric/id field.

This migration is provider-agnostic and proof-only.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / "scripts" / "provider_route_proof.py"
MARKER = "PROVIDER_ROUTE_PROOF_SLUG_IDENTITY_V16"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch() -> bool:
    text = PROOF.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False

    anchor = '''def response_value_hints(fetch: dict[str, Any]) -> list[dict[str, str]]:\n'''
    helper = '''# PROVIDER_ROUTE_PROOF_SLUG_IDENTITY_V16\ndef _provider_hint_placeholders(\n    prior_value_hints: Iterable[dict[str, Any]] | None,\n) -> dict[str, str]:\n    """Map proven prior-response values to their semantic runtime placeholder."""\n    out: dict[str, str] = {}\n    for row in prior_value_hints or []:\n        if not isinstance(row, dict):\n            continue\n        key = canonical(row.get("key"))\n        value = str(row.get("value") or "").strip()\n        if key not in PROVIDER_VALUE_KEYS or not value or len(value) < 2 or len(value) > 160:\n            continue\n        if not re.fullmatch(r"[A-Za-z0-9._~-]+", value):\n            continue\n        placeholder = "{slug}" if key == "slug" else "{id}"\n        # Prefer the more semantic slug proof when duplicate response hints carry\n        # the same literal under both a generic id and slug field.\n        if value not in out or placeholder == "{slug}":\n            out[value] = placeholder\n    return out\n\n\n'''
    text = once(text, anchor, helper + anchor, "v16-hint-placeholder-helper")

    text = once(
        text,
        '''    provider_values = _provider_hint_values(prior_value_hints)\n    method = str(fetch.get("method") or "GET").upper()\n''',
        '''    provider_values = _provider_hint_values(prior_value_hints)\n    provider_placeholders = _provider_hint_placeholders(prior_value_hints)\n    method = str(fetch.get("method") or "GET").upper()\n''',
        "v16-request-placeholder-map",
    )
    text = once(
        text,
        '''        placeholder = _request_scalar_placeholder(key, raw, fixture, provider_values)\n''',
        '''        placeholder = provider_placeholders.get(value) if value in provider_values else None\n        if placeholder is None:\n            placeholder = _request_scalar_placeholder(key, raw, fixture, provider_values)\n''',
        "v16-request-body-provider-placeholder",
    )

    text = once(
        text,
        '''    provider_values = _provider_hint_values(prior_value_hints)\n\n    tmdb = str(fixture.get("tmdbId") or "").strip()\n''',
        '''    provider_values = _provider_hint_values(prior_value_hints)\n    provider_placeholders = _provider_hint_placeholders(prior_value_hints)\n\n    tmdb = str(fixture.get("tmdbId") or "").strip()\n''',
        "v16-route-placeholder-map",
    )
    text = once(
        text,
        '''        elif decoded in provider_values:\n            placeholder = "{id}"\n''',
        '''        elif decoded in provider_values:\n            placeholder = provider_placeholders.get(decoded, "{id}")\n''',
        "v16-path-provider-placeholder",
    )
    text = once(
        text,
        '''        elif value in provider_values and key_l in PROVIDER_VALUE_KEYS:\n            placeholder = "{id}"\n        if placeholder:\n            replacement = placeholder\n''',
        '''        elif value in provider_values and key_l in PROVIDER_VALUE_KEYS:\n            placeholder = provider_placeholders.get(value, "{id}")\n        if placeholder:\n            replacement = placeholder\n''',
        "v16-query-provider-placeholder",
    )
    text = once(
        text,
        '''        "providerValueCorrelation": bool(provider_values and any(row.get("placeholder") == "{id}" for row in substitutions)),\n''',
        '''        "providerValueCorrelation": bool(provider_values and any(row.get("placeholder") in {"{id}", "{slug}"} for row in substitutions)),\n''',
        "v16-provider-correlation-semantic-placeholder",
    )

    PROOF.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else PROOF.read_text(encoding="utf-8")
    for needle in (
        MARKER,
        "def _provider_hint_placeholders",
        'placeholder = "{slug}" if key == "slug" else "{id}"',
        'provider_placeholders.get(decoded, "{id}")',
        'provider_placeholders.get(value, "{id}")',
        'row.get("placeholder") in {"{id}", "{slug}"}',
    ):
        if needle not in value:
            raise AssertionError(f"V16 route proof missing: {needle}")


def main() -> int:
    changed = patch()
    validate()
    print(
        f"PROVIDER_ROUTE_PROOF_SLUG_IDENTITY_V16_OK changed={str(changed).lower()} "
        "slug_provenance=1 opaque_id_preserved=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
