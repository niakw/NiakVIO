#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts/repair_anime_semantic_gate_20260914.py"
TEST = ROOT / "tests/global_media_type_pre_network_gate_test.py"


def patch(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    old = """    endpoint = \"/movie/\" if media_type == \"movie\" else \"/tv/\"\n    run_case(\n        patched,\n        f'''\n"""
    new = """    endpoint = \"/movie/\" if media_type == \"movie\" else \"/tv/\"\n    season_arg, episode_arg = (\"null\", \"null\") if media_type == \"movie\" else (\"1\", \"1\")\n    run_case(\n        patched,\n        f'''\n"""
    if new not in text:
        if text.count(old) != 1:
            raise AssertionError(f"{path}: semantic fixture anchor drifted")
        text = text.replace(old, new, 1)
    old_call = "const value=await provider.getStreams('{tmdb_id}','{media_type}',1,1);"
    new_call = "const value=await provider.getStreams('{tmdb_id}','{media_type}',{season_arg},{episode_arg});"
    if new_call not in text:
        if text.count(old_call) != 1:
            raise AssertionError(f"{path}: semantic fixture call drifted")
        text = text.replace(old_call, new_call, 1)
    path.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    patch(GENERATOR)
    if TEST.is_file() and "assert_live_action_stops_anime_provider" in TEST.read_text(encoding="utf-8"):
        patch(TEST)
    print("SEMANTIC_GATE_MOVIE_FIXTURE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
