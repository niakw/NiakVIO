#!/usr/bin/env python3
"""Core-wide provider security hardening with managed Core ownership.

Provider-owned bytes are hardened deterministically. The observable security
boundary is a normal NiakVIO Lego brick with transactional START/END ownership,
placed after the canonical Core boundary. Existing legacy flat boundary markers
are removed during migration.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from provider_patch_blocks import replace_managed_fix  # noqa: E402
from provider_security_hardening import assert_hardened, harden_text  # noqa: E402

HOOK_MARKER = "NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1"
HOOK_BOUNDARY = "__nuvioGlobalProviderSecurityBoundaryV1"
CORE_START_BOUNDARY = "NUVIO_GLOBAL_CORE_START_BOUNDARY_V1"
MANAGED_FIX_ID = "CORE.PROVIDER_SECURITY_BOUNDARY.V1"
TRUSTED_CORE_TAIL_MARKERS = (
    "NUVIO_GLOBAL_STREAM_FACTS_V1",
    "NUVIO_GLOBAL_STREAM_IDENTITY_V1",
    "NUVIO_GLOBAL_STREAM_PRESENTATION_V1",
)


def _split_trusted_core_tail(text: str) -> tuple[str, str]:
    """Separate provider-owned source from every NiakVIO Core brick."""
    boundary_marker = f"/* {CORE_START_BOUNDARY} */"
    boundary = text.find(boundary_marker)
    if boundary >= 0:
        return text[:boundary], text[boundary:]

    # Compatibility only for pre-boundary bundles.
    starts = [
        index
        for marker in TRUSTED_CORE_TAIL_MARKERS
        if (index := text.find(f"/* {marker}:")) >= 0
    ]
    if not starts:
        return text, ""
    start = min(starts)
    return text[:start], text[start:]


def _strip_legacy_flat_boundary(text: str) -> str:
    pattern = re.compile(
        r"/\*\s*" + re.escape(HOOK_MARKER) + r"\s*\*/\s*"
        + r"globalThis\." + re.escape(HOOK_BOUNDARY) + r"\s*=\s*true\s*;\s*"
    )
    return pattern.sub("", text)


def _managed_security_tail(core_tail: str) -> str:
    boundary_marker = f"/* {CORE_START_BOUNDARY} */"
    tail = core_tail
    if tail.startswith(boundary_marker):
        tail = tail[len(boundary_marker):]
    tail = _strip_legacy_flat_boundary(tail).lstrip()
    block_js = (
        f"/* {HOOK_MARKER} */\n"
        f"globalThis.{HOOK_BOUNDARY}=true;"
    )
    tail = replace_managed_fix(
        tail,
        MANAGED_FIX_ID,
        block_js,
        data={"revision": "managed-security-boundary-v1"},
    )
    return boundary_marker + "\n" + tail.lstrip()


def harden_bundle(text: str) -> tuple[str, dict[str, Any]]:
    """Harden provider bytes and preserve/recompose the managed Core tail."""
    provider_text, trusted_tail = _split_trusted_core_tail(text)
    provider_text = _strip_legacy_flat_boundary(provider_text)
    hardened, report = harden_text(provider_text)
    assert_hardened(hardened)
    core_tail = _managed_security_tail(trusted_tail)
    return hardened.rstrip() + "\n" + core_tail, report


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    del options
    hardened, _report = harden_bundle(text)
    return hardened
