"""Movix cleanup: keep Movix native sources and remove the old Purstream bridge."""
from __future__ import annotations

MARKER = "/* NUVIO_MOVIX_MULTI_SOURCE_V1 */"


def apply(source: str, **_kwargs) -> str:
    """Remove the legacy cross-provider shim when present.

    Purstream now has its own provider adapter. Keeping its route inside Movix
    duplicated the same 1080p stream in both tabs and made provider health
    attribution unreliable. New/upstream Movix bundles are otherwise untouched.
    """
    if MARKER not in source:
        return source
    return source.split(MARKER, 1)[0].rstrip() + "\n"
