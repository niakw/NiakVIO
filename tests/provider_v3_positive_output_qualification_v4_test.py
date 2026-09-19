#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, "scripts/upgrade_provider_v3_positive_output_qualification_v4.py"], cwd=ROOT, check=True)
sys.path.insert(0, str(ROOT / "scripts"))

from reconstruct_provider_v3_sequential_live import is_qualified


def base(required, playable, *, route_complete=True, http=True, direct=False):
    return {
        "requiredTypes": list(required),
        "validatedTypes": list(required if route_complete else []),
        "missingTypes": [] if route_complete else list(required),
        "declaredTypeCoverageRatio": 1.0 if route_complete else 0.0,
        "typeComplete": bool(route_complete),
        "playableChainValidatedTypes": list(playable),
        "providerSuccessHttp": bool(http),
        "directOutputOnly": bool(direct),
    }


# The exact old false positive: semantic route + HTTP success, but zero stream.
assert not is_qualified(base(["anime"], [], route_complete=True, http=True))

# Raw/unverified output is not represented in playableChainValidatedTypes and cannot qualify.
assert not is_qualified(base(["movie"], [], route_complete=True, http=True))

# One proven lane cannot qualify a multi-lane provider.
assert not is_qualified(base(["movie", "tv"], ["movie"], route_complete=True, http=True))

# Every declared lane playable+identity verified + route/HTTP proof qualifies.
assert is_qualified(base(["movie", "tv"], ["movie", "tv"], route_complete=True, http=True))

# Verified direct output remains supported without provider HTTP traversal.
assert is_qualified(base(["anime"], ["anime"], route_complete=True, http=False, direct=True))

# Output alone cannot bypass missing type-route/direct proof.
assert not is_qualified(base(["movie"], ["movie"], route_complete=False, http=True))

print("provider v3 positive-output qualification V4 contract passed")
