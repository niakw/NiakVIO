#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "gate_native_app_provider_selection.py"
spec = importlib.util.spec_from_file_location("native_app_provider_selection_gate", PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "native.log"
    path.write_text(
        "FIELD_NATIVE_REPOSITORY_APP_PATH client=mobile fixture=x plugins_enabled=true "
        "group_by_repository=true loaded=12 movie_enabled=8 tv_enabled=9 series_enabled=9\n",
        encoding="utf-8",
    )
    assert mod.validate_log(path, "mobile") == (12, 8, 9, 9)

    path.write_text(
        "FIELD_NATIVE_REPOSITORY_APP_PATH client=desktop fixture=x plugins_enabled=true "
        "group_by_repository=true loaded=12 movie_enabled=8 tv_enabled=9 series_enabled=0\n",
        encoding="utf-8",
    )
    try:
        mod.validate_log(path, "desktop")
    except ValueError as error:
        assert "series selection returned zero" in str(error)
    else:
        raise AssertionError("series_enabled=0 must fail the production app-path gate")

print("native app provider selection series gate tests passed")
