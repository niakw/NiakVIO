#!/usr/bin/env python3
"""Require the real Mobile/Desktop app path to select plugin providers."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

MARKER = "FIELD_NATIVE_REPOSITORY_APP_PATH"
FIELD_RE = re.compile(r"([a-z_]+)=([^\s]+)")


def parse_marker(line: str) -> dict[str, str] | None:
    if MARKER not in line:
        return None
    return {key: value for key, value in FIELD_RE.findall(line)}


def as_bool(value: str, name: str) -> bool:
    lowered = value.strip().casefold()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    raise ValueError(f"invalid {name}={value!r}")


def as_int(value: str, name: str) -> int:
    try:
        result = int(value)
    except ValueError as error:
        raise ValueError(f"invalid {name}={value!r}") from error
    if result < 0:
        raise ValueError(f"invalid {name}={value!r}")
    return result


def validate_log(path: Path, client: str) -> tuple[int, int, int, int]:
    markers = [
        parsed
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
        if (parsed := parse_marker(line)) is not None and parsed.get("client") == client
    ]
    if not markers:
        raise ValueError(f"{path}: missing {MARKER} client={client}")
    marker = markers[-1]
    plugins_enabled = as_bool(marker.get("plugins_enabled", ""), "plugins_enabled")
    loaded = as_int(marker.get("loaded", ""), "loaded")
    movie_enabled = as_int(marker.get("movie_enabled", ""), "movie_enabled")
    tv_enabled = as_int(marker.get("tv_enabled", ""), "tv_enabled")
    series_enabled = as_int(marker.get("series_enabled", ""), "series_enabled")
    if not plugins_enabled:
        raise ValueError(f"{path}: production plugin selection is globally disabled")
    if loaded <= 0:
        raise ValueError(f"{path}: repository loaded zero providers")
    if movie_enabled <= 0:
        raise ValueError(f"{path}: production movie selection returned zero providers")
    if tv_enabled <= 0:
        raise ValueError(f"{path}: production tv selection returned zero providers")
    if series_enabled <= 0:
        raise ValueError(f"{path}: production series selection returned zero providers")
    if max(movie_enabled, tv_enabled, series_enabled) > loaded:
        raise ValueError(
            f"{path}: impossible app selection loaded={loaded} movie={movie_enabled} "
            f"tv={tv_enabled} series={series_enabled}"
        )
    return loaded, movie_enabled, tv_enabled, series_enabled


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", choices=("desktop", "mobile"), required=True)
    parser.add_argument("logs", nargs="+")
    args = parser.parse_args()
    minima: tuple[int, int, int, int] | None = None
    for raw in args.logs:
        values = validate_log(Path(raw), args.client)
        minima = values if minima is None else tuple(min(a, b) for a, b in zip(minima, values))
    assert minima is not None
    print(
        "native app provider selection gate passed: "
        f"client={args.client} logs={len(args.logs)} min_loaded={minima[0]} "
        f"min_movie_enabled={minima[1]} min_tv_enabled={minima[2]} "
        f"min_series_enabled={minima[3]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
