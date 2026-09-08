#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from runtime_route_plan_cap_v1 import MAX_RUNTIME_ROUTE_PLANS, cap_runtime_routes  # noqa: E402


def row(route: str, lane: str, role: str = "search", index: int = 1) -> dict:
    return {
        "route": route,
        "semanticType": lane,
        "role": role,
        "requestIndex": index,
    }


def test_one_common_plan() -> None:
    common = "/search?q={query}"
    routes = [common, "/player/a", "/player/b", "/player/c", "/source/x"]
    data = [
        row(common, "movie"),
        row(common, "tv"),
        row(common, "anime"),
        row("/player/a", "movie", "player", 7),
        row("/player/b", "tv", "player", 7),
        row("/player/c", "anime", "player", 7),
    ]
    selected, audit = cap_runtime_routes(routes, data, {"supportedTypes": ["movie", "tv", "anime"]})
    assert selected == [common], selected
    assert audit["coveredLanes"] == ["anime", "movie", "tv"]


def test_two_movie_tv_plans() -> None:
    movie = "/movie/search?q={query}"
    tv = "/series/search?q={query}"
    routes = [movie, tv, "/embed/a", "/embed/b", "/source/a"]
    data = [
        row(movie, "movie"),
        row(tv, "tv"),
        row("/embed/a", "movie", "player", 8),
        row("/embed/b", "tv", "player", 8),
    ]
    selected, audit = cap_runtime_routes(routes, data, {"supportedTypes": ["movie", "tv"]})
    assert set(selected) == {movie, tv}, selected
    assert len(selected) == 2
    assert audit["coveredLanes"] == ["movie", "tv"]


def test_three_distinct_semantic_plans() -> None:
    movie = "/movie?q={query}"
    tv = "/series?q={query}"
    anime = "/anime?q={query}"
    routes = [movie, tv, anime, "/embed/1", "/embed/2", "/embed/3", "/source/final"]
    data = [
        row(movie, "movie"),
        row(tv, "tv"),
        row(anime, "anime"),
        row("/embed/1", "movie", "player", 9),
        row("/embed/2", "tv", "player", 9),
        row("/embed/3", "anime", "player", 9),
    ]
    selected, audit = cap_runtime_routes(routes, data, {"supportedTypes": ["movie", "tv", "anime"]})
    assert set(selected) == {movie, tv, anime}, selected
    assert len(selected) == MAX_RUNTIME_ROUTE_PLANS
    assert audit["coveredLanes"] == ["anime", "movie", "tv"]


def test_historical_overflow_is_bounded() -> None:
    routes = [f"/search/{index}?q={{query}}" for index in range(12)]
    selected, audit = cap_runtime_routes(routes, [], {"supportedTypes": ["movie", "tv", "anime"]})
    assert len(selected) == MAX_RUNTIME_ROUTE_PLANS, selected
    assert audit["before"] == 12
    assert audit["after"] == MAX_RUNTIME_ROUTE_PLANS
    assert audit["capped"] is True


def main() -> int:
    test_one_common_plan()
    test_two_movie_tv_plans()
    test_three_distinct_semantic_plans()
    test_historical_overflow_is_bounded()
    print("runtime route plan cap v1 tests passed: common=1 movie_tv=2 movie_tv_anime=3 overflow<=3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
