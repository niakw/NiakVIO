#!/usr/bin/env python3
"""Run canonical targeted repair with V21.4 immediately before live recovery."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_provider_repair_fast_targeted_v1 as runner  # noqa: E402
import upgrade_provider_episode_scoped_json_v21_4 as v214  # noqa: E402

_original_run = runner.run
_v214_applied = False


def _run_with_v214_boundary(*args: str, timeout: int | None = None) -> None:
    global _v214_applied
    if not _v214_applied and any(str(value).endswith("recover_provider_routes_from_upstreams.py") for value in args):
        v214.patch_worker()
        v214.patch_proof()
        v214.patch_recovery()
        v214.patch_materializer()
        v214.patch_base()
        v214.validate_worker()
        v214.validate_proof()
        v214.validate_recovery()
        v214.validate_materializer()
        v214.validate_base()
        _v214_applied = True
        print(
            "FIELD_PROVIDER_V21_4_BOUNDARY ready=true revision=v21.4 "
            "legacy_migrations_first=1 media_type_aware_identity=1 "
            "series_slug_role_preserved=1 episode_indexed_json_scoped=1 "
            "episode_tagged_arrays_scoped=1 missing_episode_fail_closed=1 "
            "movie_unchanged=1 numeric_quality_maps_unchanged=1 "
            "provider_specific_rules=0 all_v21_4_owners_before_census=1",
            flush=True,
        )
    _original_run(*args, timeout=timeout)


runner.run = _run_with_v214_boundary
raise SystemExit(runner.main())
