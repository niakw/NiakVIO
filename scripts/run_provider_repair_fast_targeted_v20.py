#!/usr/bin/env python3
"""Run canonical targeted repair with V20 at the correct proof boundaries."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_provider_repair_fast_targeted_v1 as runner  # noqa: E402
import upgrade_provider_response_value_correlation_v20 as v20  # noqa: E402


# Worker response hints and proof generalization must exist before the upstream
# census starts. These owners are independent of V18 materialization.
v20.patch_worker()
v20.patch_proof()
v20.validate_worker()
v20.validate_proof()

_original_run = runner.run
_post_v18_applied = False


def _run_with_v20_boundary(*args: str, timeout: int | None = None) -> None:
    global _post_v18_applied
    # The canonical runner first applies V17/V18 migrations, which create the
    # correlated-plan owners in recovery/materializer/ProviderBase. Patch those
    # exactly once immediately before the first live route census.
    if not _post_v18_applied and any(str(value).endswith("recover_provider_routes_from_upstreams.py") for value in args):
        v20.patch_recovery()
        v20.patch_materializer()
        v20.patch_base()
        v20.validate_worker()
        v20.validate_proof()
        v20.validate_recovery()
        v20.validate_materializer()
        v20.validate_base()
        _post_v18_applied = True
        print(
            "FIELD_PROVIDER_V20_BOUNDARY ready=true "
            "worker_proof_before_census=1 correlated_owners_after_v18=1",
            flush=True,
        )
    _original_run(*args, timeout=timeout)


runner.run = _run_with_v20_boundary
raise SystemExit(runner.main())
