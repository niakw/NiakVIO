#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
CORE = ROOT / "scripts" / "provider_patches" / "global_stream_identity_v1.py"

spec = importlib.util.spec_from_file_location("global_stream_identity_runtime_test", CORE)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def execute(row: dict, request: dict) -> list:
    source = "module.exports={getStreams:async()=>[" + json.dumps(row) + "]};\n"
    compiled = module.apply(source, context={"provider_id": "kehflix"})
    script = compiled + "\nmodule.exports.getStreams(" + json.dumps(request) + ").then(v=>process.stdout.write(JSON.stringify(v))).catch(e=>{console.error(e);process.exit(1)});\n"
    with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False, encoding="utf-8") as handle:
        handle.write(script)
        path = Path(handle.name)
    try:
        result = subprocess.run(["node", str(path)], text=True, capture_output=True, check=False)
    finally:
        path.unlink(missing_ok=True)
    assert result.returncode == 0, result.stdout + result.stderr
    value = json.loads(result.stdout)
    assert isinstance(value, list)
    return value


hotd_request = {
    "tmdbId": "94997",
    "mediaType": "tv",
    "title": "House of the Dragon",
    "year": 2022,
    "season": 3,
    "episode": 1,
}

# Episodic year is not identity evidence. Correct title/type/S3E1 survives even
# when the provider label exposes a season/catalogue year of 2026.
correct_episode = execute(
    {"name": "House of the Dragon S03E01 2026", "url": "https://media.example/hotd-s03e01.m3u8"},
    hotd_request,
)
assert len(correct_episode) == 1, correct_episode

# Season+episode are identity evidence and remain fail-closed when explicit.
wrong_episode = execute(
    {"name": "House of the Dragon S03E02 2026", "url": "https://media.example/hotd-s03e02.m3u8"},
    hotd_request,
)
assert wrong_episode == [], wrong_episode

# Popular 1x02 naming was previously unparsed by CORE and let explicitly
# incorrect episodes through when a provider returned a correctly titled show.
# Keep this one central identity rule for TV, mobile, desktop, and anime.
for tag in ("3x02", "03x002", "3 x 2"):
    wrong_x = execute(
        {"title": "House of the Dragon " + tag, "url": "https://media.example/opaque.m3u8"},
        hotd_request,
    )
    assert wrong_x == [], (tag, wrong_x)

correct_x = execute(
    {"title": "House of the Dragon 3x01", "url": "https://media.example/opaque.m3u8"},
    hotd_request,
)
assert len(correct_x) == 1, correct_x

# Movie year remains valid identity evidence.
wrong_movie_year = execute(
    {"name": "Interstellar 2026", "url": "https://media.example/interstellar.m3u8"},
    {"tmdbId": "157336", "mediaType": "movie", "title": "Interstellar", "year": 2014},
)
assert wrong_movie_year == [], wrong_movie_year

# A provider can return the right show title but an episode object/reader
# reference belonging to another S/E. These fields must participate in
# cross-client filtering even when the terminal CDN URL is opaque.
for wrong in (
    {"name": "House of the Dragon", "season": 3, "episode": 2, "url": "https://media.example/opaque.m3u8"},
    {"name": "House of the Dragon", "seasonNumber": "3", "episodeNumber": "2", "url": "https://media.example/opaque.m3u8"},
    {"name": "House of the Dragon EP02", "url": "https://media.example/opaque.m3u8"},
    {"name": "House of the Dragon", "url": "https://media.example/opaque.m3u8", "playerUrl": "https://reader.example/embed/12?season=3&episode=2"},
    {"name": "House of the Dragon", "url": "https://media.example/opaque.m3u8", "sourceUrl": "https://reader.example/watch?season_number=3&episode_number=2"},
):
    assert execute(wrong, hotd_request) == [], wrong

for right in (
    {"name": "House of the Dragon", "season": 3, "episode": 1, "url": "https://media.example/opaque.m3u8"},
    {"name": "House of the Dragon EP01", "url": "https://media.example/opaque.m3u8"},
    {"name": "House of the Dragon", "url": "https://media.example/opaque.m3u8", "playerUrl": "https://reader.example/embed/12?season=3&episode=1"},
    {"name": "Server 1", "url": "https://media.example/opaque.m3u8"},
):
    assert len(execute(right, hotd_request)) == 1, right

print("episodic identity runtime tests passed: provider=kehflix year=ignored S/E=authoritative movie_year=authoritative")
