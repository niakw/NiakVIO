#!/usr/bin/env python3
"""Fail native Labs when the real application path selects zero plugin providers.

Repository installation and direct PluginRepository.executeScraper(...) are useful
runtime evidence, but Mobile/Desktop production discovery first calls
getEnabledScrapersForType().  A stale profile/cache can therefore leave a visible
repository while the Streams screen starts no providers at all.  This gate consumes
FIELD_NATIVE_REPOSITORY_APP_PATH emitted by the compatibility augmenter and makes that
state blocking.
"""
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


def validate_log(path: Path, client: str) -> tuple[int, int, int]:
    markers = [
        parsed
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
        if (parsed := parse_marker(line)) is not None and parsed.get("client") == client
    ]
    if not markers:
        raise ValueError(f"{path}: missing {MARKER} client={client}")

    # One fixture should emit one current repository snapshot. If instrumentation is
    # repeated by a harness, the last marker is authoritative because it reflects the
    # final app state immediately before provider execution.
    marker = markers[-1]
    plugins_enabled = as_bool(marker.get("plugins_enabled", ""), "plugins_enabled")
    loaded = as_int(marker.get("loaded", ""), "loaded")
    movie_enabled = as_int(marker.get("movie_enabled", ""), "movie_enabled")
    tv_enabled = as_int(marker.get("tv_enabled", ""), "tv_enabled")

    if not plugins_enabled:
        raise ValueError(f"{path}: production plugin selection is globally disabled")
    if loaded <= 0:
        raise ValueError(f"{path}: repository loaded zero providers")
    if movie_enabled <= 0:
        raise ValueError(f"{path}: production movie selection returned zero providers")
    if tv_enabled <= 0:
        raise ValueError(f"{path}: production tv selection returned zero providers")
    if movie_enabled > loaded or tv_enabled > loaded:
        raise ValueError(
            f"{path}: impossible app selection loaded={loaded} movie={movie_enabled} tv={tv_enabled}"
        )
    return loaded, movie_enabled, tv_enabled


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", choices=("desktop", "mobile"), required=True)
    parser.add_argument("logs", nargs="+")
    args = parser.parse_args()

    validated = 0
    minima = {"loaded": None, "movie": None, "tv": None}
    for raw in args.logs:
        path = Path(raw)
        if not path.is_file():
            raise SystemExit(f"native app provider selection log missing: {path}")
        try:
            loaded, movie, tv = validate_log(path, args.client)
        except ValueError as error:
            raise SystemExit(f"native app provider selection gate failed: {error}") from error
        validated += 1
        minima["loaded"] = loaded if minima["loaded"] is None else min(minima["loaded"], loaded)
        minima["movie"] = movie if minima["movie"] is None else min(minima["movie"], movie)
        minima["tv"] = tv if minima["tv"] is None else min(minima["tv"], tv)

    print(
        "native app provider selection gate passed: "
        f"client={args.client} logs={validated} min_loaded={minima['loaded']} "
        f"min_movie_enabled={minima['movie']} min_tv_enabled={minima['tv']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
