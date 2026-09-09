#!/usr/bin/env python3
"""Run canonical targeted repair with V21.8 immediately before live recovery."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_provider_repair_fast_targeted_v1 as runner  # noqa: E402
import upgrade_provider_composite_request_template_v21_8 as v218  # noqa: E402
import upgrade_stream_sanitizer_v7_selection as sanitizer_v7  # noqa: E402

_original_run = runner.run
_v218_applied = False


def _run_with_v218_boundary(*args: str, timeout: int | None = None) -> None:
    global _v218_applied
    if not _v218_applied and any(str(value).endswith("recover_provider_routes_from_upstreams.py") for value in args):
        # Execute the cumulative V21.7/V7 player contract and the V21.8 generic
        # structured composite-request contract against this exact checkout before
        # the live census. Redacted/token/session values remain fail-closed.
        subprocess.run(
            [sys.executable, str(ROOT / "tests" / "provider_player_fallback_v21_7_test.py")],
            cwd=ROOT,
            check=True,
        )
        subprocess.run(
            [sys.executable, str(ROOT / "tests" / "stream_output_correlated_player_fallback_v7_test.py")],
            cwd=ROOT,
            check=True,
        )
        subprocess.run(
            [sys.executable, str(ROOT / "tests" / "provider_composite_request_template_v21_8_test.py")],
            cwd=ROOT,
            check=True,
        )
        v218.patch_worker()
        v218.patch_proof()
        v218.patch_recovery()
        v218.patch_materializer()
        v218.patch_base()
        sanitizer_v7.patch_overrides()
        sanitizer_v7.patch_hashes()
        v218.validate_worker()
        v218.validate_proof()
        v218.validate_recovery()
        v218.validate_materializer()
        v218.validate_base()
        sanitizer_v7.validate_overrides()
        sanitizer_v7.validate_hashes()
        _v218_applied = True
        print(
            "FIELD_PROVIDER_V21_8_BOUNDARY ready=true revision=v21.8 "
            "legacy_migrations_first=1 media_type_aware_identity=1 "
            "series_slug_role_preserved=1 episode_indexed_json_scoped=1 "
            "episode_tagged_arrays_scoped=1 missing_episode_fail_closed=1 "
            "initial_catalogue_only=1 matched_record_id_authoritative=1 "
            "later_response_id_learning_preserved=1 exact_source_route_lkg=1 "
            "failed_player_embed_preserved=1 later_branches_still_executed=1 "
            "correlated_player_marker=1 terminal_sanitizer_v7=1 "
            "composite_request_template=1 dotted_title=1 movie_year=1 episodic_sxxexx=1 "
            "redacted_fields_fail_closed=1 direct_media_fail_closed=1 "
            "catalogue_detail_not_promoted=1 provider_specific_rules=0 "
            "all_v21_8_owners_before_census=1",
            flush=True,
        )
    _original_run(*args, timeout=timeout)


runner.run = _run_with_v218_boundary
raise SystemExit(runner.main())
