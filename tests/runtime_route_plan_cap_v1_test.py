#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from runtime_route_plan_cap_v1 import MAX_RUNTIME_ROUTE_PLANS, cap_runtime_routes  # noqa: E402
from runtime_structured_plan_cap_v1 import MAX_STRUCTURED_PLANS, cap_structured_plans  # noqa: E402
from runtime_execution_authority_cap_v1 import MAX_AUTHORITIES, apply_selection, select_authorities  # noqa: E402


def row(route: str, lane: str, role: str = "search", index: int = 1) -> dict:
    return {"route": route, "semanticType": lane, "role": role, "requestIndex": index}


def test_one_common_plan() -> None:
    common = "/search?q={query}"
    routes = [common, "/player/a", "/player/b", "/player/c", "/source/x"]
    data = [
        row(common, "movie"), row(common, "tv"), row(common, "anime"),
        row("/player/a", "movie", "player", 7), row("/player/b", "tv", "player", 7), row("/player/c", "anime", "player", 7),
    ]
    selected, audit = cap_runtime_routes(routes, data, {"supportedTypes": ["movie", "tv", "anime"]})
    assert selected == [common], selected
    assert audit["coveredLanes"] == ["anime", "movie", "tv"]


def test_two_movie_tv_plans() -> None:
    movie = "/movie/search?q={query}"
    tv = "/series/search?q={query}"
    routes = [movie, tv, "/embed/a", "/embed/b", "/source/a"]
    data = [row(movie, "movie"), row(tv, "tv"), row("/embed/a", "movie", "player", 8), row("/embed/b", "tv", "player", 8)]
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
        row(movie, "movie"), row(tv, "tv"), row(anime, "anime"),
        row("/embed/1", "movie", "player", 9), row("/embed/2", "tv", "player", 9), row("/embed/3", "anime", "player", 9),
    ]
    selected, audit = cap_runtime_routes(routes, data, {"supportedTypes": ["movie", "tv", "anime"]})
    assert set(selected) == {movie, tv, anime}, selected
    assert len(selected) == MAX_RUNTIME_ROUTE_PLANS
    assert audit["coveredLanes"] == ["anime", "movie", "tv"]


def test_historical_overflow_is_bounded() -> None:
    routes = [f"/search/{index}?q={{query}}" for index in range(12)]
    selected, audit = cap_runtime_routes(routes, [], {"supportedTypes": ["movie", "tv", "anime"]})
    assert len(selected) == MAX_RUNTIME_ROUTE_PLANS, selected
    assert audit["before"] == 12 and audit["after"] == MAX_RUNTIME_ROUTE_PLANS and audit["capped"] is True


def structured(route: str, lane: str, role: str = "catalog-search") -> dict:
    return {
        "base": "https://catalog.example", "route": route, "requestSpec": {"method": "GET"},
        "semanticTypes": [lane], "proofModelVersion": 5, "sourceRole": role,
    }


def provider_value(lane: str) -> dict:
    return {
        "searchBase": "https://catalog.example",
        "searchRoute": "/api/search?q={query}",
        "searchRequestSpec": {"method": "GET"},
        "steps": [{"base": "https://catalog.example", "route": "/title/{id}", "requestSpec": {"method": "GET"}, "role": "detail"}],
        "semanticTypes": [lane], "proofModelVersion": 5, "sourceRole": "provider-value-correlation",
    }


def test_structured_identical_protocol_merges_to_one() -> None:
    plans = [structured("/search?q={query}", lane) for lane in ("movie", "tv", "anime")]
    selected, audit = cap_structured_plans(plans)
    assert len(selected) == 1, selected
    assert selected[0]["semanticTypes"] == ["anime", "movie", "tv"]
    assert audit["afterMerge"] == 1


def test_structured_distinct_protocols_cap_to_three() -> None:
    plans = [
        structured("/movie?q={query}", "movie"), structured("/series?q={query}", "tv"), structured("/anime?q={query}", "anime"),
        structured("/movie-alt?q={query}", "movie"), structured("/series-alt?q={query}", "tv"), structured("/anime-alt?q={query}", "anime"),
    ]
    selected, audit = cap_structured_plans(plans)
    assert len(selected) == MAX_STRUCTURED_PLANS, selected
    covered = set().union(*(set(row.get("semanticTypes") or []) for row in selected))
    assert covered == {"movie", "tv", "anime"}, covered
    assert audit["before"] == 6 and audit["after"] == 3


def test_provider_value_steps_do_not_count_as_plans() -> None:
    plan = provider_value("tv")
    plan["steps"].extend([
        {"base": "https://catalog.example", "route": "/episodes/{id}", "requestSpec": {"method": "GET"}, "role": "episode"},
        {"base": "https://catalog.example", "route": "/player/{id}", "requestSpec": {"method": "GET"}, "role": "player"},
    ])
    selected, audit = cap_structured_plans([plan])
    assert len(selected) == 1 and len(selected[0]["steps"]) == 3 and audit["after"] == 1


def test_authority_prefers_provider_value_over_duplicate_search_and_route() -> None:
    model = {
        "supportedTypes": ["tv"],
        "providerValuePlan": [provider_value("tv")],
        "searchRequestPlan": [structured("/search?q={query}", "tv")],
        "routes": ["/series/search?q={query}"],
    }
    route_data = [row("/series/search?q={query}", "tv")]
    selected, audit = select_authorities(model, route_data)
    assert len(selected) == 1, selected
    assert selected[0]["owner"] == "providerValuePlan", selected
    assert audit["coveredLanes"] == ["tv"]
    patch = {"provider_value_plan": copy.deepcopy(model["providerValuePlan"]), "search_request_plan": copy.deepcopy(model["searchRequestPlan"]), "learned_routes": list(model["routes"])}
    apply_selection(model, patch, selected)
    assert len(model.get("providerValuePlan") or []) == 1
    assert not model.get("searchRequestPlan")
    assert model.get("routes") == []


def test_authority_keeps_at_most_one_owner_per_lane_and_three_total() -> None:
    model = {
        "supportedTypes": ["movie", "tv", "anime"],
        "providerValuePlan": [provider_value("anime")],
        "apiRecipe": {"movieRoute": "/movie/{tmdbId}", "episodeRoute": "/tv/{tmdbId}/{season}/{episode}"},
        "searchRequestPlan": [structured("/search?q={query}", "movie"), structured("/search?q={query}", "tv")],
        "routes": ["/movie?q={query}", "/series?q={query}", "/anime?q={query}"],
    }
    route_data = [row("/movie?q={query}", "movie"), row("/series?q={query}", "tv"), row("/anime?q={query}", "anime")]
    selected, audit = select_authorities(model, route_data)
    assert len(selected) <= MAX_AUTHORITIES, selected
    assert audit["coveredLanes"] == ["anime", "movie", "tv"], audit
    # Correlated anime stays authoritative; API recipe covers movie/tv. Search
    # and flat-route duplicates cannot remain as extra runtime attempts.
    owners = [row["owner"] for row in selected]
    assert owners == ["providerValuePlan", "apiRecipe"], owners


def main() -> int:
    test_one_common_plan()
    test_two_movie_tv_plans()
    test_three_distinct_semantic_plans()
    test_historical_overflow_is_bounded()
    test_structured_identical_protocol_merges_to_one()
    test_structured_distinct_protocols_cap_to_three()
    test_provider_value_steps_do_not_count_as_plans()
    test_authority_prefers_provider_value_over_duplicate_search_and_route()
    test_authority_keeps_at_most_one_owner_per_lane_and_three_total()
    print("runtime plan cap v1 tests passed: evidence!=runtime routes<=3 structured<=3 one authority/lane internal steps preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
