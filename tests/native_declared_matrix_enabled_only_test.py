#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts/gate_native_declared_provider_matrix.py"


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        manifest = {
            "scrapers": [
                {"id": "hub-live", "enabled": True, "supportedTypes": ["movie", "tv"]},
                {"id": "CTGMOVIES", "enabled": False, "supportedTypes": ["movie", "tv"]},
            ]
        }
        corpus = {"native_reader_acceptance": {"fixture_by_type": {"movie": "m", "tv": "t", "anime": "a"}}}
        # Disabled CTGMOVIES is deliberately present as error telemetry. It must
        # neither be required nor become an unexpected quality route.
        log = "\n".join([
            "FIELD_NATIVE_PROVIDER_BEGIN client=tv provider=hub-live request_type=movie",
            "FIELD_NATIVE_RESULT client=tv provider=hub-live request_type=movie count=1",
            "FIELD_NATIVE_PROVIDER_BEGIN client=tv provider=hub-live request_type=tv",
            "FIELD_NATIVE_RESULT client=tv provider=hub-live request_type=tv count=1",
            "FIELD_NATIVE_PROVIDER_BEGIN client=tv provider=CTGMOVIES request_type=movie",
            "FIELD_NATIVE_ERROR client=tv provider=CTGMOVIES request_type=movie error=hard-timeout",
        ]) + "\n"
        (d / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (d / "corpus.json").write_text(json.dumps(corpus), encoding="utf-8")
        (d / "lab.log").write_text(log, encoding="utf-8")
        cp = subprocess.run(
            [sys.executable, str(GATE), "--client", "tv", "--manifest", str(d / "manifest.json"), "--corpus", str(d / "corpus.json"), str(d / "lab.log")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if cp.returncode != 0:
            raise AssertionError(cp.stdout + cp.stderr)
        assert "state=passed" in cp.stdout, cp.stdout
        assert "providers=1" in cp.stdout and "disabled=1" in cp.stdout, cp.stdout
        assert "excluded_from_quality_gate=true" in cp.stdout, cp.stdout
        print("NATIVE_DECLARED_MATRIX_ENABLED_ONLY_OK active=1 disabled_debt=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
