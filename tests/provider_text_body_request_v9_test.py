#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import provider_route_proof as proof  # noqa: E402


def fixture() -> dict:
    return {
        "fixture": {
            "title": "Interstellar",
            "tmdbId": "157336",
            "mediaType": "movie",
            "year": 2014,
        }
    }


def main() -> int:
    # JSON-array-looking raw text is intentionally still bodyKind=text; the
    # abstracted template, not the raw fixture title, becomes executable DATA.
    fetch = {
        "method": "POST",
        "body_kind": "text",
        "body_values": {"$text": '["Interstellar"]'},
        "proof_headers": {"content-type": "application/json"},
    }
    spec, meta = proof.derive_request_spec(fetch, fixture())
    assert meta.get("requestSpecReusable") is True, meta
    assert spec == {
        "method": "POST",
        "headers": {"content-type": "application/json"},
        "bodyKind": "text",
        "body": '["{query}"]',
    }, spec

    # Opaque static text has no proof-backed identity substitution and must stay
    # diagnostic-only rather than becoming a replayable request.
    opaque, opaque_meta = proof.derive_request_spec({
        "method": "POST",
        "body_kind": "text",
        "body_values": {"$text": "static-command"},
        "proof_headers": {"content-type": "text/plain"},
    }, fixture())
    assert opaque is None, opaque
    assert opaque_meta.get("requestSpecReusable") is False, opaque_meta

    # Redacted/sensitive evidence can never become executable.
    redacted, redacted_meta = proof.derive_request_spec({
        "method": "POST",
        "body_kind": "text",
        "body_values": {"$text": "<redacted>"},
        "proof_headers": {},
    }, fixture())
    assert redacted is None, redacted
    assert redacted_meta.get("requestSpecReusable") is False, redacted_meta

    base = (ROOT / "scripts" / "provider_base_store.py").read_text(encoding="utf-8")
    assert "NIAKVIO_PROVIDER_BASE_TEXT_BODY_REQUEST_V9" in base
    assert 'bodyKind === "text"' in base
    assert "spec.body = _recipeExpandScalar(raw.body, values)" in base

    print("provider text body request v9 tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
