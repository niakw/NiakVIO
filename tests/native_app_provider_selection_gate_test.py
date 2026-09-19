#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("gate",ROOT/"scripts/gate_native_app_provider_selection.py");mod=importlib.util.module_from_spec(spec);assert spec.loader;spec.loader.exec_module(mod)
with tempfile.TemporaryDirectory() as td:
    p=Path(td)/"ok.log";p.write_text("FIELD_NATIVE_REPOSITORY_APP_PATH client=mobile fixture=x plugins_enabled=true group_by_repository=true loaded=12 movie_enabled=8 tv_enabled=9 series_enabled=9\n",encoding="utf-8")
    assert mod.validate(p,"mobile")== (12,8,9,9)
    p.write_text("FIELD_NATIVE_REPOSITORY_APP_PATH client=desktop fixture=x plugins_enabled=true group_by_repository=true loaded=12 movie_enabled=8 tv_enabled=9 series_enabled=0\n",encoding="utf-8")
    try:mod.validate(p,"desktop")
    except ValueError as e:assert "series=0" in str(e)
    else:raise AssertionError("series=0 must fail")
print("native app provider selection series gate tests passed")
