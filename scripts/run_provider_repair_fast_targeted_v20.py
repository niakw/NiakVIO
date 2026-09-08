#!/usr/bin/env python3
"""Run canonical targeted repair with V21 immediately before live recovery."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_provider_repair_fast_targeted_v1 as runner  # noqa: E402
import upgrade_provider_shared_player_trace_v21 as v21  # noqa: E402

_original_run = runner.run
_v21_applied = False


def _run_with_v21_boundary(*args: str, timeout: int | None = None) -> None:
    global _v21_applied
    # Preserve the complete legacy migration sequence unchanged. V21 composes
    # strict V20.5.1 value semantics with the shared player decoder + bounded
    # runtime trace only at the boundary before the live upstream census.
    if not _v21_applied and any(str(value).endswith("recover_provider_routes_from_upstreams.py") for value in args):
        v21.patch_worker()
        v21.patch_proof()
        v21.patch_recovery()
        v21.patch_materializer()
        v21.patch_base()
        v21.validate_worker()
        v21.validate_proof()
        v21.validate_recovery()
        v21.validate_materializer()
        v21.validate_base()
        _v21_applied = True
        print(
            "FIELD_PROVIDER_V21_BOUNDARY ready=true revision=v21 "
            "legacy_migrations_first=1 v20_5_1_semantics=1 "
            "strict_id_slug_readiness=1 dependency_passes=1 "
            "correlated_depth=8 nested_json_http_values=1 "
            "obfuscated_hls_decoder=1 decoy_hls_rejected=1 "
            "bounded_value_trace=48 provider_specific_rules=0 "
            "all_v21_owners_before_census=1",
            flush=True,
        )
    _original_run(*args, timeout=timeout)


runner.run = _run_with_v21_boundary
raise SystemExit(runner.main())
