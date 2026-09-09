#!/usr/bin/env python3
"""Run canonical targeted repair with V21.5 immediately before live recovery."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_provider_repair_fast_targeted_v1 as runner  # noqa: E402
import upgrade_provider_catalogue_identity_correlation_v21_5 as v215  # noqa: E402

_original_run = runner.run
_v215_applied = False


def _run_with_v215_boundary(*args: str, timeout: int | None = None) -> None:
    global _v215_applied
    if not _v215_applied and any(str(value).endswith("recover_provider_routes_from_upstreams.py") for value in args):
        v215.patch_worker()
        v215.patch_proof()
        v215.patch_recovery()
        v215.patch_materializer()
        v215.patch_base()
        v215.validate_worker()
        v215.validate_proof()
        v215.validate_recovery()
        v215.validate_materializer()
        v215.validate_base()
        _v215_applied = True
        print(
            "FIELD_PROVIDER_V21_5_BOUNDARY ready=true revision=v21.5 "
            "legacy_migrations_first=1 media_type_aware_identity=1 "
            "series_slug_role_preserved=1 episode_indexed_json_scoped=1 "
            "episode_tagged_arrays_scoped=1 missing_episode_fail_closed=1 "
            "movie_unchanged=1 numeric_quality_maps_unchanged=1 "
            "initial_catalogue_only=1 matched_record_id_authoritative=1 "
            "onclick_card_correlation=1 later_response_id_learning_preserved=1 "
            "global_id_fallback_preserved=1 provider_specific_rules=0 "
            "all_v21_5_owners_before_census=1",
            flush=True,
        )
    _original_run(*args, timeout=timeout)


runner.run = _run_with_v215_boundary
raise SystemExit(runner.main())
