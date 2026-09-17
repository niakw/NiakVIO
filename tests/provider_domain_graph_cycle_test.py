#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validate_provider_domain_graph import validate_patch


def expect_ok(name: str, patch: dict) -> None:
    errors = validate_patch(name, patch)
    assert not errors, (name, errors)


def expect_error(name: str, patch: dict, needle: str) -> None:
    errors = validate_patch(name, patch)
    assert errors, (name, "expected an error")
    assert any(needle in error for error in errors), (name, needle, errors)


def main() -> int:
    expect_ok(
        "valid-aliases",
        {
            "official_site": "https://flemmix.cloud",
            "domain_substitutions": {"flemmix.men": "flemmix.cloud"},
            "replacements": {"flemmix.me": "flemmix.cloud"},
            "runtime_domain_replacements": {
                "flemmix.vip": "flemmix.cloud",
                "flemmix.ws": "flemmix.cloud",
            },
        },
    )

    expect_error(
        "cross-map-cycle",
        {
            "official_site": "https://flemmix.cloud",
            "domain_substitutions": {"flemmix.men": "flemmix.cloud"},
            "replacements": {"flemmix.me": "flemmix.cloud"},
            "runtime_domain_replacements": {"flemmix.cloud": "flemmix.me"},
        },
        "combined domain cycle",
    )

    expect_error(
        "canonical-outgoing",
        {
            "official_site": "https://flemmix.cloud",
            "runtime_domain_replacements": {"flemmix.cloud": "flemmix.me"},
        },
        "canonical host flemmix.cloud has outgoing domain edge",
    )

    # Full-path/text replacements are not domain-authority edges and therefore
    # must not create false cycles merely because their URLs share a host.
    expect_ok(
        "path-replacement-ignored",
        {
            "official_site": "https://example.com",
            "replacements": {
                "https://example.com/old/path": "https://example.com/new/path",
                "some literal": "another literal",
            },
        },
    )

    # Same-host aliases are harmless for cycle analysis; another validator may
    # still reject them as redundant metadata.
    expect_ok(
        "same-host-no-graph-edge",
        {
            "official_site": "https://example.com",
            "domain_substitutions": {"https://example.com": "example.com"},
        },
    )

    print("PROVIDER_DOMAIN_GRAPH_CYCLE_TEST_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
