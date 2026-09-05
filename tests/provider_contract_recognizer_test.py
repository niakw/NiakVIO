#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import provider_contract_recognizer as r


# Gowaru-style modular Anime-Sama: POST catalogue search + typed episodes.js path.
anime_sama = r'''
const BASE_URL = "https://anime-sama.to";
async function searchSlugsScored(query) {
  return fetchText(`${BASE_URL}/template-php/defaut/fetch.php`, {
    method: 'POST', headers: {'Content-Type':'application/x-www-form-urlencoded','Referer':BASE_URL},
    body: `query=${encodeURIComponent(query)}`
  });
}
async function fetchJs(slug, seasonPath, lang) {
  const url = `${BASE_URL}/catalogue/${slug}/${seasonPath}/${lang}/episodes.js`;
  return fetchText(url);
}
export async function extractStreams(tmdbId, mediaType, season, episode) {
  const titles = await getTmdbTitles(tmdbId, mediaType, {season});
  if (mediaType === 'movie') return fetchJs('x','film','vf');
  return fetchJs('x',`saison${season}`,'vostfr');
}
'''
routes = r.extract_routes(anime_sama)
assert "/template-php/defaut/fetch.php" in routes, routes
assert any("/catalogue/" in route and "episodes.js" in route for route in routes), routes
contracts = r.recognize_request_contracts(anime_sama, routes)
search = next(row for row in contracts if row["route"] == "/template-php/defaut/fetch.php")
assert search["method"] == "POST", search
assert search["formEncoded"] is True, search
assert "query" in search["bodyFields"], search
assert r.infer_family(anime_sama, routes, contracts) == "catalogue-episodes-js"
input_contract = r.recognize_input_contract(anime_sama)
assert input_contract["acceptsTmdbId"] is True
assert "tmdb-metadata" in input_contract["metadataDependencies"]
assert "movie" in input_contract["typeEvidence"]


# Yoru template: method/interface evidence must not invent executable provider routes.
yoru_template = r'''
export async function extractStreams(tmdbId, mediaType, season, episode) { return []; }
async function getStreams(tmdbId, mediaType, season, episode) {
  return extractStreams(tmdbId, mediaType, season, episode);
}
'''
assert r.extract_routes(yoru_template) == []
yoru_input = r.recognize_input_contract("", yoru_template)
assert yoru_input["acceptsTmdbId"] is True
assert yoru_input["acceptsSeasonEpisode"] is True
assert yoru_input["templateInterfaceEvidence"] is True


# Frenchstream/DLE family: POST search, season lookup and eps_<id>.txt must be recognized.
dle = r'''
const root='https://fs16.lol';
async function find(query){
  return fetch(root + '/engine/ajax/search.php', {
    method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded','Referer':root},
    body:'query='+encodeURIComponent(query)+'&page=1'
  });
}
async function tv(id, season){
  const a = await fetch(`/engine/ajax/get_seasons.php?serie_tag=s-${id}&news_id=0`);
  const b = await fetch(`/data/eps_${season}.txt`);
  return [a,b];
}
const news='?newsid=123';
'''
dle_routes = r.extract_routes(dle)
dle_contracts = r.recognize_request_contracts(dle, dle_routes)
assert "/engine/ajax/search.php" in dle_routes, dle_routes
assert any("get_seasons.php" in route for route in dle_routes), dle_routes
assert any("/data/eps_" in route for route in dle_routes), dle_routes
assert r.infer_family(dle, dle_routes, dle_contracts) == "dle-film-api"
assert any(row["route"] == "/engine/ajax/search.php" and row["method"] == "POST" for row in dle_contracts)


# Kehflix-like source plan: title -> player -> streams route must remain distinct.
kehflix = r'''
async function getStreams(tmdbId, mediaType, season, episode) {
  const title = await fetch(`/title/${tmdbId}?type=${mediaType}`);
  const player = await fetch(`/player?id=${tmdbId}&type=${mediaType}`);
  return fetch(`/api/streams/episode?id=${tmdbId}&season=${season}&episode=${episode}`);
}
'''
keh_routes = r.extract_routes(kehflix)
assert any(route.startswith("/title/") for route in keh_routes), keh_routes
assert any(route.startswith("/player") for route in keh_routes), keh_routes
assert any("/api/streams/episode" in route for route in keh_routes), keh_routes
assert r.infer_family(kehflix, keh_routes, r.recognize_request_contracts(kehflix, keh_routes)) == "signed-player-api"


# Minified/compiled bundle: literals near fetch calls still become request contracts.
aio = "async function g(e){let r=await fetch('/search?q='+encodeURIComponent(e));return fetch('/api/source?id='+e)}"
aio_routes = r.extract_routes(aio)
assert any(route.startswith("/search?q=") for route in aio_routes), aio_routes
assert any(route.startswith("/api/source?id=") for route in aio_routes), aio_routes
aio_contracts = r.recognize_request_contracts(aio, aio_routes)
assert any(row["role"] == "search" for row in aio_contracts), aio_contracts
assert any(row["role"] in {"api", "source"} for row in aio_contracts), aio_contracts


# Junk/static infrastructure must never become executable Provider DATA.
for junk in ("/resolvers.js", "/wp-json/oembed/1.0/embed", "/wp-admin/admin-ajax.php", "/images/logo.png"):
    assert r.route_is_junk(junk), junk
assert not r.route_is_executable_candidate("/catalogue/")
assert r.route_is_executable_candidate("/?s={query}")

print("provider contract recognizer tests passed")
