#!/usr/bin/env python3
"""Run the canonical targeted repair after applying V20 response correlation."""
from __future__ import annotations

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Apply before the canonical runner performs route recovery. The migration is
# idempotent and validates every modified owner itself.
runpy.run_path(str(ROOT / "scripts" / "upgrade_provider_response_value_correlation_v20.py"), run_name="__main__")
runpy.run_path(str(ROOT / "tests" / "provider_response_value_correlation_v20_test.py"), run_name="__main__")
runpy.run_path(str(ROOT / "scripts" / "run_provider_repair_fast_targeted_v1.py"), run_name="__main__")
