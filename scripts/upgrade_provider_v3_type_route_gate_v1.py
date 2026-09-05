#!/usr/bin/env python3
"""Prevent arbitrary successful homepage queries from proving a provider media type."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "validate_provider_v3_routes_sequential.py"
OLD = '''def _generic_control_route(route: str) -> bool:\n    value = str(route or "").strip().casefold()\n    if not value or value == "/":\n        return True\n    if route_role(value) == "search":\n        return True\n    if re.search(r"/(?:status|health|healthz|ping)(?:[/?#]|$)", value):\n        return True\n    try:\n        parsed = urllib.parse.urlsplit(value)\n        path = parsed.path or value.split("?", 1)[0]\n    except ValueError:\n        path = value.split("?", 1)[0]\n'''
NEW = '''def _generic_control_route(route: str) -> bool:\n    value = str(route or "").strip().casefold()\n    if not value:\n        return True\n    try:\n        parsed = urllib.parse.urlsplit(value)\n        path = parsed.path or "/"\n    except ValueError:\n        path = value.split("?", 1)[0] or "/"\n    # A homepage remains a generic control surface even when arbitrary query\n    # parameters are accepted.  /?tmdbId=... returning 200 is not proof that\n    # the provider implements a typed movie/TV route.\n    if path in {"", "/"}:\n        return True\n    if route_role(value) == "search":\n        return True\n    if re.search(r"/(?:status|health|healthz|ping)(?:[/?#]|$)", value):\n        return True\n'''


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if NEW in text:
        return False
    if text.count(OLD) != 1:
        raise AssertionError(f"type-route generic control anchor count={text.count(OLD)}")
    TARGET.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    return True


def validate() -> None:
    text = TARGET.read_text(encoding="utf-8")
    if NEW not in text:
        raise AssertionError("root-query control-route guard missing")
    if 'if path in {"", "/"}:' not in text:
        raise AssertionError("root path must remain generic regardless of query")


def main() -> int:
    changed = patch()
    validate()
    print(
        "PROVIDER_V3_TYPE_ROUTE_GATE_V1_OK "
        f"changed={str(changed).lower()} root_query=not_type_proof"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
