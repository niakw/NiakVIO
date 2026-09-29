#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_provider_targeted_recovery.py"
PROBE = ROOT / "scripts" / "nuvio_tv_probe_tmdb_ci.cjs"

spec = importlib.util.spec_from_file_location("targeted_recovery_shape", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

shape = mod.compact_response_shape({
    "kind": "html",
    "sampleBytes": 12345,
    "anchors": 42,
    "classTokens": [
        "card-item", "movie_card", "x", "123bad", "bad token",
        "A" * 60, "episode-row",
    ],
    "idTokens": ["results", "download-list", "1bad", "bad token"],
    "markers": ["download", "episode", "not-allowed"],
})
assert shape["classTokens"] == ["card-item", "movie_card", "episode-row"], shape
assert shape["idTokens"] == ["results", "download-list"], shape
assert shape["markers"] == ["download", "episode"], shape
serialized = str(shape)
assert "bad token" not in serialized
assert "123bad" not in serialized
assert "not-allowed" not in serialized

src = PROBE.read_text(encoding="utf-8")
assert "function structuralTokens(" in src
assert "classTokens:structuralTokens(raw,'class',16)" in src
assert "idTokens:structuralTokens(raw,'id',12)" in src
assert "response bodies remain ephemeral and are never stored" in src

start = src.index("function structuralTokens(")
end = src.index("function textShape(", start)
helper = src[start:end]
html = '<div id="results" class="movie-card item item"></div><a class="episode-row item"></a>'
node = subprocess.run(
    [
        "node",
        "-e",
        helper
        + "\nconst html=process.argv[1];"
        + "\nconsole.log(JSON.stringify({classes:structuralTokens(html,'class',16),ids:structuralTokens(html,'id',12)}));",
        html,
    ],
    capture_output=True,
    text=True,
    check=True,
)
tokens = json.loads(node.stdout.strip())
assert tokens["classes"] == ["item", "episode-row", "movie-card"], tokens
assert tokens["ids"] == ["results"], tokens

print("Provider response-shape structural privacy contract passed")
