#!/usr/bin/env python3
"""Run canonical targeted repair with V20.3 immediately before live recovery."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_provider_repair_fast_targeted_v1 as runner  # noqa: E402
import upgrade_provider_response_value_correlation_v20_3 as v20  # noqa: E402

_original_run = runner.run
_v20_applied = False


def _run_with_v20_boundary(*args: str, timeout: int | None = None) -> None:
    global _v20_applied
    # Preserve the complete legacy migration sequence unchanged. V20.3 composes
    # with the final V11/V18/V20.2 owners only at the boundary immediately before
    # the first upstream census consumes provider responses.
    if not _v20_applied and any(str(value).endswith("recover_provider_routes_from_upstreams.py") for value in args):
        v20.patch_worker()
        v20.patch_proof()
        v20.patch_recovery()
        v20.patch_materializer()
        v20.patch_base()
        v20.validate_worker()
        v20.validate_proof()
        v20.validate_recovery()
        v20.validate_materializer()
        v20.validate_base()
        _v20_applied = True
        print(
            "FIELD_PROVIDER_V20_BOUNDARY ready=true revision=v20.3 "
            "legacy_migrations_first=1 v18_4_resolver_composed=1 "
            "slug_python_projection=1 urlencoded_search_form=1 all_v20_owners_before_census=1",
            flush=True,
        )
    _original_run(*args, timeout=timeout)


runner.run = _run_with_v20_boundary
raise SystemExit(runner.main())
