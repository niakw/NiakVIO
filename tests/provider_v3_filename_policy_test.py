#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from provider_v3_filename_policy import matches_provider_v3_filename

SHA = "a" * 64

workspace_report = {"context": "workspace", "publication": False}
published_report = {"context": "main", "publication": True}
stale_workspace_report = {"context": "workspace", "publication": False}

assert matches_provider_v3_filename(
    "anime-sama", "anime-sama-aaaaaaaaaaaaaaaa.js", SHA, workspace_report,
    execution_context="workspace",
)
assert not matches_provider_v3_filename(
    "anime-sama", "anime-sama--nuvio--aaaaaaaaaaaaaaaa.js", SHA, workspace_report,
    execution_context="workspace",
)

assert matches_provider_v3_filename(
    "anime-sama", "anime-sama--nuvio--aaaaaaaaaaaaaaaa.js", SHA, published_report,
    execution_context="publication",
)
assert matches_provider_v3_filename(
    "anime-sama", "anime-sama--published-baseline--aaaaaaaaaaaaaaaa.js", SHA, published_report,
    execution_context="release",
)
assert not matches_provider_v3_filename(
    "anime-sama", "anime-sama-aaaaaaaaaaaaaaaa.js", SHA, published_report,
    execution_context="publication",
)

# A stale workspace provenance report must never downgrade a public audit when the
# execution context is unspecified. Unspecified remains fail-closed publication.
os.environ.pop("NUVIO_PROVIDER_V3_CONTEXT", None)
assert matches_provider_v3_filename(
    "anime-sama", "anime-sama--nuvio--aaaaaaaaaaaaaaaa.js", SHA, stale_workspace_report
)
assert not matches_provider_v3_filename(
    "anime-sama", "anime-sama-aaaaaaaaaaaaaaaa.js", SHA, stale_workspace_report
)

# Environment context is the real workspace authority used by route-proof CI.
os.environ["NUVIO_PROVIDER_V3_CONTEXT"] = "workspace"
try:
    assert matches_provider_v3_filename(
        "anime-sama", "anime-sama-aaaaaaaaaaaaaaaa.js", SHA, stale_workspace_report
    )
    assert not matches_provider_v3_filename(
        "anime-sama", "anime-sama--nuvio--aaaaaaaaaaaaaaaa.js", SHA, stale_workspace_report
    )
finally:
    os.environ.pop("NUVIO_PROVIDER_V3_CONTEXT", None)

assert not matches_provider_v3_filename(
    "anime-sama", "anime-sama--nuvio--bbbbbbbbbbbbbbbb.js", SHA, published_report,
    execution_context="publication",
)
assert not matches_provider_v3_filename(
    "anime-sama", "../anime-sama--nuvio--aaaaaaaaaaaaaaaa.js", "bad", published_report,
    execution_context="publication",
)

print("provider v3 filename policy tests passed: explicit workspace, public fail-closed, stale report ignored")
