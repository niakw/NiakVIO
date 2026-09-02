#!/usr/bin/env python3
"""Preventive security Lego inside the single Provider envelope.

Security is composed during the run as a managed CORE.* block. It never rewrites
ProviderBase, provider DATA, provider-specific Lego, or final bytes after build.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from provider_patch_blocks import (  # noqa: E402
    PROVIDER_BEGIN_MARKER,
    PROVIDER_END_MARKER,
    replace_managed_fix,
)

HOOK_MARKER = "NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1"
HOOK_BOUNDARY = "__nuvioGlobalProviderSecurityBoundaryV1"
MANAGED_FIX_ID = "CORE.PROVIDER_SECURITY_BOUNDARY.V1"


def harden_bundle(text: str) -> tuple[str, dict[str, Any]]:
    """Compatibility name: compose only the preventive Core security Lego."""
    source = str(text or "")
    if source.count(PROVIDER_BEGIN_MARKER) != 1 or source.count(PROVIDER_END_MARKER) != 1:
        raise ValueError("security Lego requires exactly one Provider envelope")

    block_js = (
        f"/* {HOOK_MARKER} */\n"
        f"globalThis.{HOOK_BOUNDARY}=true;"
    )
    output = replace_managed_fix(
        source,
        MANAGED_FIX_ID,
        block_js,
        data={
            "revision": "preventive-core-security-v4",
            "providerMutation": False,
            "postBuildMutation": False,
        },
    )
    return output, {
        "changed": output != source,
        "providerMutation": False,
        "postBuildMutation": False,
        "mode": "preventive-core-lego",
    }


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    del options
    output, _report = harden_bundle(text)
    return output
