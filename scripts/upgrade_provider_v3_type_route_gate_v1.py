#!/usr/bin/env python3
"""Prevent arbitrary successful homepage queries from proving a provider media type.

The original V1 made every root-query URL generic. A later, stricter query-route
contract permits only reusable typed identity templates such as
`/?tmdbId={tmdbId}&type=movie`. This upgrader must therefore be idempotent across
both source states and must never downgrade the newer contract.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "validate_provider_v3_routes_sequential.py"
QUERY_IDENTITY_MARKER = "PROVIDER_V3_QUERY_IDENTITY_ROUTE_V1"
OLD = '''def _generic_control_route(route: str) -> bool:\n    value = str(route or "").strip().casefold()\n    if not value or value == "/":\n        return True\n    if route_role(value) == "search":\n        return True\n    if re.search(r"/(?:status|health|healthz|ping)(?:[/?#]|$)", value):\n        return True\n    try:\n        parsed = urllib.parse.urlsplit(value)\n        path = parsed.path or value.split("?", 1)[0]\n    except ValueError:\n        path = value.split("?", 1)[0]\n'''
NEW = '''def _generic_control_route(route: str) -> bool:\n    value = str(route or "").strip().casefold()\n    if not value:\n        return True\n    try:\n        parsed = urllib.parse.urlsplit(value)\n        path = parsed.path or "/"\n    except ValueError:\n        path = value.split("?", 1)[0] or "/"\n    # A homepage remains a generic control surface even when arbitrary query\n    # parameters are accepted.  /?tmdbId=... returning 200 is not proof that\n    # the provider implements a typed movie/TV route.\n    if path in {"", "/"}:\n        return True\n    if route_role(value) == "search":\n        return True\n    if re.search(r"/(?:status|health|healthz|ping)(?:[/?#]|$)", value):\n        return True\n'''


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    # Newer contract supersedes this textual V1 patch. It is stricter than a
    # blanket allow: only reusable identity + explicit semantic type escapes the
    # generic-homepage guard. Never overwrite it with the older blanket rule.
    if QUERY_IDENTITY_MARKER in text:
        validate_text(text)
        return False
    if NEW in text:
        validate_text(text)
        return False
    if text.count(OLD) != 1:
        raise AssertionError(f"type-route generic control anchor count={text.count(OLD)}")
    text = text.replace(OLD, NEW, 1)
    TARGET.write_text(text, encoding="utf-8")
    validate_text(text)
    return True


def validate_text(text: str) -> None:
    if QUERY_IDENTITY_MARKER in text:
        required = (
            'has_reusable_identity = any(',
            'has_semantic_type = any(',
            'if path in {"", "/"} and not (has_reusable_identity and has_semantic_type):',
        )
        for needle in required:
            if needle not in text:
                raise AssertionError(f"typed root-query control guard missing: {needle}")
        return
    if NEW not in text:
        raise AssertionError("root-query control-route guard missing")
    if 'if path in {"", "/"}:' not in text:
        raise AssertionError("root path must remain generic regardless of query")


def validate() -> None:
    validate_text(TARGET.read_text(encoding="utf-8"))


def main() -> int:
    changed = patch()
    text = TARGET.read_text(encoding="utf-8")
    mode = "typed-reusable-identity-only" if QUERY_IDENTITY_MARKER in text else "all-root-query-generic"
    print(
        "PROVIDER_V3_TYPE_ROUTE_GATE_V1_OK "
        f"changed={str(changed).lower()} root_query={mode}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
