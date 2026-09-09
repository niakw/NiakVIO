#!/usr/bin/env python3
"""Run canonical targeted repair with V21.3 immediately before live recovery."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_provider_repair_fast_targeted_v1 as runner  # noqa: E402
import upgrade_provider_series_slug_role_v21_3 as v213  # noqa: E402

_original_run = runner.run
_v213_applied = False


def _run_with_v213_boundary(*args: str, timeout: int | None = None) -> None:
    global _v213_applied
    if not _v213_applied and any(str(value).endswith("recover_provider_routes_from_upstreams.py") for value in args):
        v213.patch_worker()
        v213.patch_proof()
        v213.patch_recovery()
        v213.patch_materializer()
        v213.patch_base()
        v213.validate_worker()
        v213.validate_proof()
        v213.validate_recovery()
        v213.validate_materializer()
        v213.validate_base()
        _v213_applied = True
        print(
            "FIELD_PROVIDER_V21_3_BOUNDARY ready=true revision=v21.3 "
            "legacy_migrations_first=1 v21_player_trace=1 "
            "media_type_aware_identity=1 series_numeric_installment_reject=1 "
            "movie_year_strict=1 tracking_provider_ids_rejected=1 "
            "self_contained_title_identity=1 legacy_v20_5_compatible=1 "
            "series_slug_role_preserved=1 episode_slug_handoff_allowed=1 "
            "provider_specific_rules=0 all_v21_3_owners_before_census=1",
            flush=True,
        )
    _original_run(*args, timeout=timeout)


runner.run = _run_with_v213_boundary
raise SystemExit(runner.main())
