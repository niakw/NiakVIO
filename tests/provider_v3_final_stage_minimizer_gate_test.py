#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import materialize_provider_v3_all as allmat


def setenv(name: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value


def main() -> int:
    old_context = os.environ.get("NUVIO_PROVIDER_V3_CONTEXT")
    old_final = os.environ.get(allmat.FINAL_MINIMIZER_ENV)
    try:
        setenv("NUVIO_PROVIDER_V3_CONTEXT", "workspace")
        setenv(allmat.FINAL_MINIMIZER_ENV, None)
        assert allmat.materialization_context() == "workspace"
        assert allmat.final_minimizer_enabled("workspace") is False

        setenv(allmat.FINAL_MINIMIZER_ENV, "1")
        try:
            allmat.final_minimizer_enabled("workspace")
        except ValueError as exc:
            assert "final-stage only" in str(exc)
        else:
            raise AssertionError("workspace minimization must be rejected")

        setenv("NUVIO_PROVIDER_V3_CONTEXT", "release")
        setenv(allmat.FINAL_MINIMIZER_ENV, None)
        assert allmat.final_minimizer_enabled("release") is False
        setenv(allmat.FINAL_MINIMIZER_ENV, "1")
        assert allmat.final_minimizer_enabled("release") is True

        setenv("NUVIO_PROVIDER_V3_CONTEXT", "main")
        assert allmat.final_minimizer_enabled("main") is True

        one = (ROOT / "scripts" / "materialize_provider_v3_one.py").read_text(encoding="utf-8")
        all_text = (ROOT / "scripts" / "materialize_provider_v3_all.py").read_text(encoding="utf-8")
        assert "PROVIDER_V3_FINAL_STAGE_MINIMIZER_GATE_V1" in one
        assert "PROVIDER_V3_FINAL_STAGE_MINIMIZER_GATE_V1" in all_text
        assert '"skippedReason": "final-stage-only"' in one
        assert '"skippedReason": "final-stage-only"' in all_text
        print("PROVIDER_V3_FINAL_STAGE_MINIMIZER_GATE_TEST_OK workspace=false release=opt-in main=opt-in")
        return 0
    finally:
        setenv("NUVIO_PROVIDER_V3_CONTEXT", old_context)
        setenv(allmat.FINAL_MINIMIZER_ENV, old_final)


if __name__ == "__main__":
    raise SystemExit(main())
