#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import provider_contract_recognizer as r
from provider_route_expression_analyzer import install as install_route_analyzer

install_route_analyzer(r)


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


# Interface-only source must never invent executable provider routes.
template_interface = r'''
export async function extractStreams(tmdbId, mediaType, season, episode) { return []; }
async function getStreams(tmdbId, mediaType, season, episode) {
  return extractStreams(tmdbId, mediaType, season, episode);
}
'''
assert r.extract_routes(template_interface) == []
template_input = r.recognize_input_contract("", template_interface)
assert template_input["acceptsTmdbId"] is True
assert template_input["acceptsSeasonEpisode"] is True
assert template_input["templateInterfaceEvidence"] is True


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


# Compiled bundle literals near fetch calls still become request contracts.
aio = "async function g(e){let r=await fetch('/search?q='+encodeURIComponent(e));return fetch('/api/source?id='+e)}"
aio_routes = r.extract_routes(aio)
assert any(route.startswith("/search?q=") for route in aio_routes), aio_routes
assert any(route.startswith("/api/source?id=") for route in aio_routes), aio_routes

aio_contracts = r.recognize_request_contracts(aio, aio_routes)
assert any(row["role"] == "search" for row in aio_contracts), aio_contracts
assert any(row["role"] in {"api", "source"} for row in aio_contracts), aio_contracts


# AnimeKai-shaped route construction: base + browser query, then result.url + episode suffix.
# The analyzer must recover paths from expressions, not require one static URL literal.
animekai_shape = r'''
const BASE = 'https://www3.example.invalid';
async function searchProvider(query) {
  const endpoint = BASE + '/browser?keyword=' + encodeURIComponent(query);
  return fetch(endpoint, {headers:{'Referer':BASE}});
}
async function watchEpisode(result, episode) {
  const watchUrl = result.url + '/ep-' + episode;
  const html = await fetch(watchUrl, {headers:{Referer:BASE}});
  const embed = html.match(/data-video="([^"]+)/);
  return embed;
}
'''
animekai_routes = r.extract_routes(animekai_shape)
assert "/browser?keyword={query}" in animekai_routes, animekai_routes
assert "/ep-{episode}" in animekai_routes, animekai_routes
animekai_contracts = r.recognize_request_contracts(animekai_shape, animekai_routes)
assert any(row["route"] == "/browser?keyword={query}" and row["executedEvidence"] for row in animekai_contracts), animekai_contracts
assert any(row["route"] == "/ep-{episode}" and row["refererRequired"] for row in animekai_contracts), animekai_contracts


# AnimeZey-shaped worker API: endpoint assembled through a variable, POST JSON body
# passed through a helper, Referer required. Object keys must survive the helper layer.
animezey_shape = r'''
async function postSearch(payload) {
  const searchPath = '/api/search';
  const endpoint = 'https://' + workerDomain + searchPath;
  return fetchPlain(endpoint, {
    method: 'POST',
    headers: {'content-type':'application/json', Referer:endpoint},
    body: JSON.stringify(payload)
  });
}
async function searchEpisodes(query) {
  return postSearch({q: query, page_token: null, page_index: 0});
}
async function searchMovies(query) {
  return postSearch({q: query});
}
'''
animezey_routes = r.extract_routes(animezey_shape)
assert "/api/search" in animezey_routes, animezey_routes
animezey_contracts = r.recognize_request_contracts(animezey_shape, animezey_routes)
az_search = next(row for row in animezey_contracts if row["route"] == "/api/search")
assert az_search["method"] == "POST", az_search
assert az_search.get("jsonEncoded") is True, az_search
assert az_search["refererRequired"] is True, az_search
assert {"q", "page_token", "page_index"}.issubset(set(az_search["bodyFields"])), az_search
assert az_search["executedEvidence"] is True, az_search


# Bounded static string decoding: useful route strings may be recovered from a
# common custom-base64 table without executing the decoder/rotation JavaScript.
obfuscated_shape = r'''
const alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=';
const table=['L2FwaS9zZWFyY2g','aHR0cHM6Ly93b3JrZXIuZXhhbXBsZS9hcGkvc2VhcmNo'];
function decoder(i){ return table[i]; }
'''
obfuscated_routes = r.extract_routes(obfuscated_shape)
assert "/api/search" in obfuscated_routes, obfuscated_routes
obfuscated_contracts = r.recognize_request_contracts(obfuscated_shape, obfuscated_routes)
obfuscated_search = next(row for row in obfuscated_contracts if row["route"] == "/api/search")
assert obfuscated_search["executedEvidence"] is False, obfuscated_search
assert obfuscated_search.get("evidence") == "decoded-static-string", obfuscated_search


# Anime-Ultime-shaped catalogue/player knowledge already present in NiakVIO DATA.
# A player endpoint plus typed catalogue evidence must remain a usable route family.
anime_ultime_shape = r'''
const BASE='https://v5.example.invalid';
async function search(query) {
  const endpoint = BASE + '/search?query=' + encodeURIComponent(query);
  return fetchText(endpoint, {headers:{Referer:BASE}});
}
async function player(id) {
  const endpoint = BASE + '/VideoPlayer.html?id=' + id;
  return fetchText(endpoint, {headers:{Referer:BASE}});
}
'''
au_routes = r.extract_routes(anime_ultime_shape)
assert "/search?query={query}" in au_routes, au_routes
assert "/VideoPlayer.html?id={id}" in au_routes, au_routes
au_contracts = r.recognize_request_contracts(anime_ultime_shape, au_routes)
assert any(row["role"] == "search" and row["executedEvidence"] for row in au_contracts), au_contracts
assert any(row["role"] == "player" and row["executedEvidence"] for row in au_contracts), au_contracts


# Junk/static infrastructure must never become executable Provider DATA.
for junk in ("/resolvers.js", "/wp-json/oembed/1.0/embed", "/wp-admin/admin-ajax.php", "/images/logo.png"):
    assert r.route_is_junk(junk), junk
assert not r.route_is_executable_candidate("/catalogue/")
assert r.route_is_executable_candidate("/?s={query}")

print("provider contract recognizer tests passed")
