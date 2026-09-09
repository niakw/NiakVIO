#!/usr/bin/env python3
"""Run canonical targeted repair with V21.6 immediately before live recovery."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_provider_repair_fast_targeted_v1 as runner  # noqa: E402
import upgrade_provider_player_fallback_v21_6 as v216  # noqa: E402

_original_run = runner.run
_v216_applied = False


def _run_with_v216_boundary(*args: str, timeout: int | None = None) -> None:
    global _v216_applied
    if not _v216_applied and any(str(value).endswith("recover_provider_routes_from_upstreams.py") for value in args):
        v216.patch_worker()
        v216.patch_proof()
        v216.patch_recovery()
        v216.patch_materializer()
        v216.patch_base()
        v216.validate_worker()
        v216.validate_proof()
        v216.validate_recovery()
        v216.validate_materializer()
        v216.validate_base()
        _v216_applied = True
        print(
            "FIELD_PROVIDER_V21_6_BOUNDARY ready=true revision=v21.6 "
            "legacy_migrations_first=1 media_type_aware_identity=1 "
            "series_slug_role_preserved=1 episode_indexed_json_scoped=1 "
            "episode_tagged_arrays_scoped=1 missing_episode_fail_closed=1 "
            "initial_catalogue_only=1 matched_record_id_authoritative=1 "
            "later_response_id_learning_preserved=1 exact_source_route_lkg=1 "
            "failed_player_embed_preserved=1 later_branches_still_executed=1 "
            "catalogue_detail_not_promoted=1 provider_specific_rules=0 "
            "all_v21_6_owners_before_census=1",
            flush=True,
        )
    _original_run(*args, timeout=timeout)


runner.run = _run_with_v216_boundary
raise SystemExit(runner.main())
