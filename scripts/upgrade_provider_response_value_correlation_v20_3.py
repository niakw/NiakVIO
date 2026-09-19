#!/usr/bin/env python3
"""V20.3: preserve provider-value plans end-to-end, including encoded POST search.

V20.2 fixed the V18.4 runtime resolver composition, but two generic projection
holes remained visible in live proof:

1. V18's Python DATA materializer still filtered provider-value steps with an
   id-only predicate. A proof-owned ``{slug}`` step therefore survived recovery
   but disappeared from the materialized Provider MODEL.
2. Some providers submit an ``application/x-www-form-urlencoded`` search body as
   a raw string. V9 safely captured that string but compared the percent-encoded
   bytes directly with the decoded fixture title, so a positive search could be
   marked non-reusable and the whole search -> provider-id chain was discarded.

V20.3 fixes both boundaries without provider-specific rules. URL-encoded text is
parsed as form data, each decoded scalar is abstracted through the existing
request placeholder policy, and replay is emitted as the existing ``form``
requestSpec. Sensitive/residual values still fail closed.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import upgrade_provider_response_value_correlation_v20_2 as v202  # noqa: E402

PROOF = v202.legacy.PROOF
BASE = v202.legacy.BASE
MARKER = "PROVIDER_RESPONSE_VALUE_CORRELATION_V20_3"
BASE_MARKER = "NIAKVIO_PROVIDER_RESPONSE_VALUE_PROJECTION_V20_3"

patch_worker = v202.patch_worker
patch_recovery = v202.patch_recovery
patch_materializer = v202.patch_materializer
validate_worker = v202.validate_worker
validate_recovery = v202.validate_recovery
validate_materializer = v202.validate_materializer


def _once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_proof() -> bool:
    # V20.2 must own the current proof shape first.
    v202.patch_proof()
    text = PROOF.read_text(encoding="utf-8")
    if MARKER in text:
        validate_proof(text)
        return False

    anchor = "def derive_request_spec(\n"
    helper = r'''# PROVIDER_RESPONSE_VALUE_CORRELATION_V20_3

def _urlencoded_text_body_spec(
    raw: object,
    fixture: dict[str, Any],
    provider_values: set[str],
) -> tuple[dict[str, Any] | None, list[dict[str, str]], list[dict[str, str]]]:
    """Abstract a bounded x-www-form-urlencoded raw body as ordinary form DATA."""
    text = str(raw if raw is not None else "")
    if not text or len(text) > 1024 or "<redacted>" in text:
        return None, [], [{"location": "body:$text", "value": "unsafe-or-empty"}]
    try:
        pairs = urllib.parse.parse_qsl(text, keep_blank_values=True, strict_parsing=False)
    except (TypeError, ValueError):
        return None, [], [{"location": "body:$text", "value": "invalid-urlencoded-form"}]
    if not pairs or len(pairs) > 32:
        return None, [], [{"location": "body:$text", "value": "invalid-urlencoded-form"}]

    body: dict[str, Any] = {}
    substitutions: list[dict[str, str]] = []
    residue: list[dict[str, str]] = []
    fixture_tokens = unique([
        fixture.get("tmdbId"), fixture.get("title"), fixture.get("year"),
        fixture.get("season"), fixture.get("episode"), *provider_values,
    ], 32)

    for raw_key, raw_value in pairs:
        key = str(raw_key or "").strip()
        value = str(raw_value if raw_value is not None else "")
        if not key or len(key) > 96 or len(value) > 512:
            residue.append({"location": "body:$text", "value": "invalid-urlencoded-field"})
            continue
        placeholder = _request_scalar_placeholder(key, value, fixture, provider_values)
        if placeholder:
            body[key] = placeholder
            substitutions.append({
                "location": f"body:{key}",
                "value": value[:160],
                "placeholder": placeholder,
            })
            continue
        if any(token and str(token) in value for token in fixture_tokens):
            residue.append({"location": f"body:{key}", "value": value[:160]})
            continue
        body[key] = value

    # A raw body gains execution authority only when at least one value was
    # correlated to current fixture/provider DATA. Static opaque POST bodies stay
    # diagnostic-only exactly as in V9.
    if not substitutions:
        residue.append({"location": "body:$text", "value": "no-proof-backed-substitution"})
    if residue:
        return None, substitutions, residue[:20]
    return body, substitutions, []


'''
    text = _once(text, anchor, helper + anchor, "v20.3-urlencoded-helper")

    old = '''    elif body_kind == "text":
        text_template, text_substitutions, text_residue = _text_body_template(
            raw_body.get("$text"), fixture, provider_values
        )
        substitutions.extend(text_substitutions)
        residue.extend(text_residue)
        reusable = reusable and text_template is not None and not text_residue
        if text_template is not None:
            spec["bodyKind"] = "text"
            spec["body"] = text_template
'''
    new = '''    elif body_kind == "text":
        # V20.3: the worker can only know that a JS string body is text. The
        # Content-Type proves when that text is actually URL-encoded form data.
        content_type = next((
            str(value or "").strip().casefold()
            for key, value in raw_headers.items()
            if canonical(key) == "content-type"
        ), "")
        if "application/x-www-form-urlencoded" in content_type:
            form_body, form_substitutions, form_residue = _urlencoded_text_body_spec(
                raw_body.get("$text"), fixture, provider_values
            )
            substitutions.extend(form_substitutions)
            residue.extend(form_residue)
            reusable = reusable and form_body is not None and not form_residue
            if form_body is not None:
                spec["bodyKind"] = "form"
                spec["body"] = form_body
        else:
            text_template, text_substitutions, text_residue = _text_body_template(
                raw_body.get("$text"), fixture, provider_values
            )
            substitutions.extend(text_substitutions)
            residue.extend(text_residue)
            reusable = reusable and text_template is not None and not text_residue
            if text_template is not None:
                spec["bodyKind"] = "text"
                spec["body"] = text_template
'''
    text = _once(text, old, new, "v20.3-urlencoded-proof-branch")
    PROOF.write_text(text, encoding="utf-8")
    validate_proof(text)
    return True


def patch_base() -> bool:
    # First apply all current V20.2 runtime/base changes.
    v202.patch_base()
    text = BASE.read_text(encoding="utf-8")
    if BASE_MARKER in text:
        validate_base(text)
        return False

    old = '''                    and "{id}" in str(step.get("route") or "")
'''
    new = '''                    # NIAKVIO_PROVIDER_RESPONSE_VALUE_PROJECTION_V20_3
                    and ("{id}" in str(step.get("route") or "") or "{slug}" in str(step.get("route") or ""))
'''
    if old in text:
        text = _once(text, old, new, "v20.3-python-provider-value-id-or-slug")
    elif (
        '"{id}" in str(step.get("route") or "") or "{slug}" in str(step.get("route") or "")'
        not in text
    ):
        raise AssertionError("V20.3 provider-value Python projection anchor missing")

    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return True


def validate_proof(text: str | None = None) -> None:
    v202.validate_proof(text)
    value = text if text is not None else PROOF.read_text(encoding="utf-8")
    for needle in (
        MARKER,
        "def _urlencoded_text_body_spec",
        "urllib.parse.parse_qsl",
        '"application/x-www-form-urlencoded" in content_type',
        'spec["bodyKind"] = "form"',
        "_request_scalar_placeholder(key, value, fixture, provider_values)",
    ):
        if needle not in value:
            raise AssertionError(f"V20.3 proof missing {needle}")


def validate_base(text: str | None = None) -> None:
    v202.validate_base(text)
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    if BASE_MARKER not in value:
        raise AssertionError("V20.3 Python provider-value projection marker missing")
    if 'and "{id}" in str(step.get("route") or "")\n' in value:
        raise AssertionError("V20.3 retains id-only Python provider-value step filter")
    if '"{slug}" in str(step.get("route") or "")' not in value:
        raise AssertionError("V20.3 slug provider-value projection missing")


def main() -> int:
    changed = (
        patch_worker()
        | patch_proof()
        | patch_recovery()
        | patch_materializer()
        | patch_base()
    )
    validate_worker()
    validate_proof()
    validate_recovery()
    validate_materializer()
    validate_base()
    print(
        f"PROVIDER_RESPONSE_VALUE_CORRELATION_V20_3_OK changed={str(changed).lower()} "
        "slug_python_projection=1 urlencoded_text_form_replay=1 "
        "sensitive_residue_fail_closed=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
