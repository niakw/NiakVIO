#!/usr/bin/env python3
"""Run canonical targeted repair with V21.1 immediately before live recovery."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_provider_repair_fast_targeted_v1 as runner  # noqa: E402
import upgrade_provider_media_identity_guard_v21_1 as v211  # noqa: E402

_original_run = runner.run
_v211_applied = False


def _run_with_v211_boundary(*args: str, timeout: int | None = None) -> None:
    global _v211_applied
    if not _v211_applied and any(str(value).endswith("recover_provider_routes_from_upstreams.py") for value in args):
        v211.patch_worker()
        v211.patch_proof()
        v211.patch_recovery()
        v211.patch_materializer()
        v211.patch_base()
        v211.validate_worker()
        v211.validate_proof()
        v211.validate_recovery()
        v211.validate_materializer()
        v211.validate_base()
        _v211_applied = True
        print(
            "FIELD_PROVIDER_V21_1_BOUNDARY ready=true revision=v21.1 "
            "legacy_migrations_first=1 v21_player_trace=1 "
            "media_type_aware_identity=1 series_numeric_installment_reject=1 "
            "movie_year_strict=1 tracking_provider_ids_rejected=1 "
            "provider_specific_rules=0 all_v21_1_owners_before_census=1",
            flush=True,
        )
    _original_run(*args, timeout=timeout)


runner.run = _run_with_v211_boundary
raise SystemExit(runner.main())
