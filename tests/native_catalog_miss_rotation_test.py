#!/usr/bin/env python3
from __future__ import annotations

import base64
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/native_catalog_miss_rotation.py"


def b64(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    log = root / "route.log"
    providers = root / "providers.txt"
    fixture = root / "fixture.txt"
    report = root / "report.json"
    log.write_text(
        "\n".join([
            f"FIELD_NATIVE_RESULT client=desktop fixture=interstellar provider64={b64('clean-zero')} count=0 route_mode=declared",
            f"FIELD_NATIVE_RESULT client=desktop fixture=interstellar provider64={b64('positive')} count=2 route_mode=declared",
            f"FIELD_NATIVE_RESULT client=desktop fixture=interstellar provider64={b64('errored')} count=0 route_mode=declared",
            f"FIELD_NATIVE_ERROR client=desktop fixture=interstellar provider64={b64('errored')} error64={b64('boom')}",
            f"FIELD_NATIVE_RESULT client=desktop fixture=interstellar provider64={b64('probe-only')} count=0 route_mode=capability_probe",
            f"FIELD_NATIVE_PROVIDER_SKIPPED client=desktop fixture=interstellar provider64={b64('skipped')} reason=unsupported",
        ]) + "\n",
        encoding="utf-8",
    )
    subprocess.run([
        sys.executable, str(SCRIPT),
        "--fixture", "interstellar",
        "--log", str(log),
        "--seed", "rotation-test",
        "--providers-out", str(providers),
        "--fixture-out", str(fixture),
        "--json-out", str(report),
    ], cwd=ROOT, check=True)
    assert providers.read_text(encoding="utf-8").splitlines() == ["clean-zero"]
    next_fixture = fixture.read_text(encoding="utf-8").strip()
    assert next_fixture and next_fixture != "interstellar"

print("NATIVE_CATALOG_MISS_ROTATION_OK clean_zero_rotates=true errors_stop=true positive_stops=true capability_probe_ignored=true")
