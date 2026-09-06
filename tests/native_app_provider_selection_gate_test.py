#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts/gate_native_app_provider_selection.py"
spec = importlib.util.spec_from_file_location("native_app_provider_selection_gate", PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def marker(client: str = "desktop", *, enabled: str = "true", loaded: int = 96, movie: int = 80, tv: int = 72) -> str:
    return (
        f"FIELD_NATIVE_REPOSITORY_APP_PATH client={client} fixture=interstellar "
        f"plugins_enabled={enabled} group_by_repository=false loaded={loaded} "
        f"movie_enabled={movie} tv_enabled={tv}\n"
    )


with tempfile.TemporaryDirectory() as raw_tmp:
    tmp = Path(raw_tmp)
    good = tmp / "good.log"
    good.write_text(marker(), encoding="utf-8")
    assert module.validate_log(good, "desktop") == (96, 80, 72)

    # The last marker is authoritative when a long-lived Lab stages the same route
    # more than once.
    repeated = tmp / "repeated.log"
    repeated.write_text(marker(movie=1, tv=1) + marker(movie=80, tv=72), encoding="utf-8")
    assert module.validate_log(repeated, "desktop") == (96, 80, 72)

    bad_cases = {
        "missing": "FIELD_NATIVE_REPOSITORY_LOAD_RESULT client=desktop loaded=96\n",
        "disabled": marker(enabled="false"),
        "zero-loaded": marker(loaded=0, movie=0, tv=0),
        "zero-movie": marker(movie=0),
        "zero-tv": marker(tv=0),
        "impossible": marker(loaded=2, movie=3, tv=1),
    }
    for name, text in bad_cases.items():
        path = tmp / f"{name}.log"
        path.write_text(text, encoding="utf-8")
        try:
            module.validate_log(path, "desktop")
        except ValueError:
            pass
        else:
            raise AssertionError(f"{name} must fail closed")

print("native app provider selection gate tests passed")
