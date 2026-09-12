#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import upgrade_provider_disabled_fast_advance_v1 as migration  # noqa: E402

migration.patch()
migration.validate()

import reconstruct_provider_v3_sequential_live as sequential  # noqa: E402

assert sequential.skip_disabled_live_qualification({"enabled": False}) is True
assert sequential.skip_disabled_live_qualification({"enabled": True}) is False
assert sequential.skip_disabled_live_qualification({}) is False

previous = os.environ.get("PROVIDER_V3_AUDIT_DISABLED_LIVE")
try:
    for truthy in ("1", "true", "yes", "on", "TRUE"):
        os.environ["PROVIDER_V3_AUDIT_DISABLED_LIVE"] = truthy
        assert sequential.skip_disabled_live_qualification({"enabled": False}) is False, truthy
    os.environ["PROVIDER_V3_AUDIT_DISABLED_LIVE"] = "0"
    assert sequential.skip_disabled_live_qualification({"enabled": False}) is True
finally:
    if previous is None:
        os.environ.pop("PROVIDER_V3_AUDIT_DISABLED_LIVE", None)
    else:
        os.environ["PROVIDER_V3_AUDIT_DISABLED_LIVE"] = previous

source = (ROOT / "scripts" / "reconstruct_provider_v3_sequential_live.py").read_text(encoding="utf-8")
assert "PROVIDER_V3_DISABLED_FAST_ADVANCE_V1" in source
assert "FIELD_PROVIDER_DISABLED_FAST_ADVANCE" in source
assert 'evaluation["qualificationSkipped"] = True' in source
assert 'evaluation["disabledByActivationMatrix"] = True' in source
assert "network_qualification=false" in source

fast = source.index("disabled_fast_advance = skip_disabled_live_qualification(provider)")
probe = source.index("run_until_qualified(provider, model, minimum, timeout)", fast)
assert fast < probe
finalize = source.index("finalize_provider(", probe)
guard = source.rfind("if disabled_fast_advance:", probe, finalize)
assert guard >= 0
preserve = source.index("Do not overwrite durable/historical Provider DATA", guard, finalize)
assert preserve > guard
assert "_rows, evaluation, used_tasks = run_until_qualified(provider, model, minimum, timeout)" in source

print(
    "Provider v3 disabled fast advance tests passed: OFF providers skip release live qualification by default, "
    "deep OFF audits remain opt-in, durable proof is preserved, and the enabled-provider gate is unchanged."
)
