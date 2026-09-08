#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from runtime_route_plan_cap_v1 import NORMAL_ENTRY_PLAN_TARGET, cap_runtime_routes  # noqa: E402
from runtime_structured_plan_cap_v1 import NORMAL_STRUCTURED_PLAN_TARGET, cap_structured_plans  # noqa: E402
from runtime_execution_authority_cap_v1 import apply_selection, select_authorities  # noqa: E402


def row(route: str, lane: str, role: str = "search", index: int = 1, fixture: str = "fixture") -> dict:
    return {"route": route, "semanticType": lane, "role": role, "requestIndex": index, "fixture": fixture}


def test_simple_duplicate_entry_routes_can_be_compacted() -> None:
    routes = [f"/search-{index}?q={{query}}" for index in range(6)]
    data = [row(route, "movie", "search", index) for index, route in enumerate(routes)]
    selected, audit = cap_runtime_routes(routes, data, {"supportedTypes": ["movie"]})
    assert len(selected) == 1, selected
    assert audit["optimized"] is True
    assert audit["targetExceeded"] is False


def test_one_common_semantic_entry_is_preferred_when_safe() -> None:
    common = "/search?q={query}"
    routes = [common, "/movie?q={query}", "/series?q={query}", "/anime?q={query}"]
    data = [
        row(common, "movie", fixture="movie"),
        row(common, "tv", fixture="tv"),
        row(common, "anime", fixture="anime"),
        row("/movie?q={query}", "movie", fixture="movie-alt"),
        row("/series?q={query}", "tv", fixture="tv-alt"),
        row("/anime?q={query}", "anime", fixture="anime-alt"),
    ]
    selected, audit = cap_runtime_routes(routes, data, {"supportedTypes": ["movie", "tv", "anime"]})
    assert selected == [common], selected
    assert audit["coveredLanes"] == ["anime", "movie", "tv"]


def test_historical_overflow_without_proof_is_preserved() -> None:
    routes = [f"/search/{index}?q={{query}}" for index in range(12)]
    selected, audit = cap_runtime_routes(routes, [], {"supportedTypes": ["movie", "tv", "anime"]})
    assert selected == routes
    assert audit["targetExceeded"] is True
    assert audit["exceptionReason"] == "insufficient-proof-to-collapse"


def test_frenchstream_like_search_detail_player_fanout_is_preserved() -> None:
    search = "/index.php?do=search&subaction=search&story={query}"
    detail = "/films/{slug}.html"
    players = [f"/player/{index}/{{id}}" for index in range(1, 5)]
    sources = [f"/source/{index}/{{id}}" for index in range(1, 5)]
    routes = [search, detail, *players, *sources]
    data = [
        row(search, "movie", "search", 0, "interstellar"),
        row(detail, "movie", "detail", 1, "interstellar"),
        *[row(route, "movie", "player", index + 2, "interstellar") for index, route in enumerate(players)],
        *[row(route, "movie", "source", index + 6, "interstellar") for index, route in enumerate(sources)],
    ]
    selected, audit = cap_runtime_routes(routes, data, {"supportedTypes": ["movie", "tv"]})
    assert selected == routes, selected
    assert len(selected) > NORMAL_ENTRY_PLAN_TARGET
    assert audit["targetExceeded"] is True
    assert audit["exceptionReason"] == "multi-hop-fanout"


def test_four_genuinely_distinct_entry_plans_are_not_forced_to_three() -> None:
    routes = [f"/catalog-{index}?q={{query}}" for index in range(4)]
    # Each route is the only proven entry for a different fixture/protocol. With
    # no safe proof that they are interchangeable, the policy must keep them.
    data = [
        row(routes[0], "movie", "search", 0, "movie-a"),
        row(routes[1], "movie", "search", 0, "movie-b"),
        row(routes[2], "movie", "search", 0, "movie-c"),
        row(routes[3], "movie", "detail", 0, "movie-d"),
    ]
    # The current heuristic can compact same-lane pure search alternatives only
    # when semantic coverage proves interchangeability. Make one route downstream
    # mixed so this case is explicitly non-collapsible.
    data.append(row(routes[3], "movie", "player", 1, "movie-d"))
    selected, audit = cap_runtime_routes(routes, data, {"supportedTypes": ["movie"]})
    assert selected == routes
    assert audit["targetExceeded"] is True
    assert audit["exceptionReason"] in {"multi-stage-chain", "mixed-entry-and-downstream-routes"}


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


def test_structured_distinct_protocols_beyond_three_are_preserved() -> None:
    plans = [
        structured("/movie?q={query}", "movie"), structured("/series?q={query}", "tv"), structured("/anime?q={query}", "anime"),
        structured("/movie-alt?q={query}", "movie"), structured("/series-alt?q={query}", "tv"), structured("/anime-alt?q={query}", "anime"),
    ]
    selected, audit = cap_structured_plans(plans)
    assert len(selected) == 6, selected
    assert audit["targetExceeded"] is True
    assert audit["normalTarget"] == NORMAL_STRUCTURED_PLAN_TARGET


def test_provider_value_steps_do_not_count_as_plans() -> None:
    plan = provider_value("tv")
    plan["steps"].extend([
        {"base": "https://catalog.example", "route": "/episodes/{id}", "requestSpec": {"method": "GET"}, "role": "episode"},
        {"base": "https://catalog.example", "route": "/player/{id}", "requestSpec": {"method": "GET"}, "role": "player"},
        {"base": "https://catalog.example", "route": "/source/{id}", "requestSpec": {"method": "GET"}, "role": "source"},
    ])
    selected, audit = cap_structured_plans([plan])
    assert len(selected) == 1 and len(selected[0]["steps"]) == 4 and audit["after"] == 1


def test_authority_ranking_is_non_destructive() -> None:
    model = {
        "supportedTypes": ["tv"],
        "providerValuePlan": [provider_value("tv")],
        "searchRequestPlan": [structured("/search?q={query}", "tv")],
        "routes": ["/series/search?q={query}"],
    }
    route_data = [row("/series/search?q={query}", "tv")]
    preferred, audit = select_authorities(model, route_data)
    assert preferred and preferred[0]["owner"] == "providerValuePlan", preferred
    assert audit["coveredLanes"] == ["tv"]
    before = copy.deepcopy(model)
    patch = {"provider_value_plan": copy.deepcopy(model["providerValuePlan"]), "search_request_plan": copy.deepcopy(model["searchRequestPlan"]), "learned_routes": list(model["routes"])}
    apply_selection(model, patch, preferred)
    assert model == before
    assert len(model.get("searchRequestPlan") or []) == 1
    assert model.get("routes") == ["/series/search?q={query}"]


def test_authority_preference_can_cover_three_lanes_without_deleting_fallbacks() -> None:
    model = {
        "supportedTypes": ["movie", "tv", "anime"],
        "providerValuePlan": [provider_value("anime")],
        "apiRecipe": {"movieRoute": "/movie/{tmdbId}", "episodeRoute": "/tv/{tmdbId}/{season}/{episode}"},
        "searchRequestPlan": [structured("/search?q={query}", "movie"), structured("/search?q={query}", "tv")],
        "routes": ["/movie?q={query}", "/series?q={query}", "/anime?q={query}"],
    }
    route_data = [row("/movie?q={query}", "movie"), row("/series?q={query}", "tv"), row("/anime?q={query}", "anime")]
    preferred, audit = select_authorities(model, route_data)
    assert audit["coveredLanes"] == ["anime", "movie", "tv"], audit
    assert audit["allEvidenceBackedAuthoritiesPreserved"] is True
    assert len(model["routes"]) == 3 and len(model["searchRequestPlan"]) == 2


def main() -> int:
    test_simple_duplicate_entry_routes_can_be_compacted()
    test_one_common_semantic_entry_is_preferred_when_safe()
    test_historical_overflow_without_proof_is_preserved()
    test_frenchstream_like_search_detail_player_fanout_is_preserved()
    test_four_genuinely_distinct_entry_plans_are_not_forced_to_three()
    test_structured_identical_protocol_merges_to_one()
    test_structured_distinct_protocols_beyond_three_are_preserved()
    test_provider_value_steps_do_not_count_as_plans()
    test_authority_ranking_is_non_destructive()
    test_authority_preference_can_cover_three_lanes_without_deleting_fallbacks()
    print("runtime route policy v2 tests passed: normal target=3, complex/fanout exceptions preserved, authority ranking non-destructive")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
