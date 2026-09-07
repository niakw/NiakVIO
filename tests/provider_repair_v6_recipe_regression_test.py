#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import recover_provider_routes_from_upstreams as recovery  # noqa: E402


def row(*, route: str, origin: str, role: str, semantic: str, index: int,
        streams: int = 0, last: int | None = None, request: dict | None = None) -> dict:
    return {
        "route": route,
        "origin": origin,
        "role": role,
        "semanticType": semantic,
        "requestIndex": index,
        "requestSpecReusable": True,
        "requestSpec": request or {"method": "GET"},
        "taskStreamCount": streams,
        "taskRawStreamCount": streams,
        "taskLastRequestIndex": index if last is None else last,
    }


# A typed TMDB API with both movie and episodic routes must never synthesize a
# generic directRoute from the movie request: directRoute executes first in the
# common runtime and would make TV requests call type=movie.
playimdb = recovery.build_simple_api_recipe([
    row(
        route="/api.php?tmdb={tmdbId}&type=movie",
        origin="https://streamdata.vaplayer.ru",
        role="api",
        semantic="movie",
        index=0,
        streams=3,
    ),
    row(
        route="/api.php?tmdb={tmdbId}&type=tv&season={season}&episode={episode}",
        origin="https://streamdata.vaplayer.ru",
        role="api",
        semantic="tv",
        index=0,
        streams=3,
    ),
])
assert playimdb is not None
assert "directRoute" not in playimdb, playimdb
assert "type=movie" in playimdb.get("movieRoute", "")
assert "type=tv" in playimdb.get("episodeRoute", "")


# Shared metadata helpers observed before a positive provider request are
# evidence context only. The body-search provider request is the executable
# terminal request when it is last in the positive task.
animesama = recovery.build_simple_api_recipe([
    row(
        route="/api/v2/themoviedb?id={tmdbId}",
        origin="https://arm.haglund.dev",
        role="api",
        semantic="anime",
        index=0,
        streams=1,
        last=2,
    ),
    row(
        route="/meta/series/tt12343534.json",
        origin="https://v3-cinemeta.strem.io",
        role="detail",
        semantic="anime",
        index=1,
        streams=1,
        last=2,
    ),
    row(
        route="/template-php/defaut/fetch.php",
        origin="https://animesama.co",
        role="detail",
        semantic="anime",
        index=2,
        streams=1,
        last=2,
        request={"method": "POST", "bodyKind": "form", "body": {"query": "{query}"}},
    ),
])
assert animesama is not None, animesama
assert animesama.get("base") == "https://animesama.co", animesama
assert animesama.get("directRoute") == "/template-php/defaut/fetch.php", animesama
assert animesama.get("directRequest", {}).get("body", {}).get("query") == "{query}", animesama
assert "arm.haglund.dev" not in str(animesama)
assert "v3-cinemeta.strem.io" not in str(animesama)


# A positive task does not make an early search request terminal. If later
# provider/player requests were observed, flattening the search into directRoute
# would discard the actual resolver chain.
animekai = recovery.build_simple_api_recipe([
    row(
        route="/browser?keyword={query}",
        origin="https://www3.anikai.cc",
        role="search",
        semantic="anime",
        index=0,
        streams=15,
        last=19,
    ),
    row(
        route="/embed/kaxbateqdn76",
        origin="https://otakuvid.online",
        role="player",
        semantic="anime",
        index=19,
        streams=15,
        last=19,
    ),
])
assert animekai is None, animekai


# True one-request terminal search APIs remain supported.
terminal = recovery.build_simple_api_recipe([
    row(
        route="/?s={query}",
        origin="https://provider.example",
        role="search",
        semantic="movie",
        index=0,
        streams=2,
        last=0,
    ),
])
assert terminal is not None, terminal
assert terminal.get("directRoute") == "/?s={query}", terminal
assert terminal.get("terminalSearchProof") is True, terminal

print("provider repair v6 recipe regressions passed")
