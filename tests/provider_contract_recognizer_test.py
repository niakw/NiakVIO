#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import provider_contract_recognizer as r
from provider_route_normalization_guard import install as install_route_guard
from provider_route_role_classifier import install as install_route_roles
from provider_route_expression_analyzer import install as install_route_analyzer

# Recognition is one composite engine: normalization guard first, then route-role
# and expression analysis. Tests deliberately use the same install order as the
# production local enricher so the raw recognizer cannot silently bypass guards.
install_route_guard(r)
install_route_roles(r)
install_route_analyzer(r)
assert getattr(r, "_NIAKVIO_ROUTE_NORMALIZATION_GUARD_INSTALLED", False)
assert getattr(r, "_NIAKVIO_ROUTE_ROLE_CLASSIFIER_INSTALLED", False)
assert getattr(r, "_NIAKVIO_ROUTE_ANALYZER_INSTALLED", False)


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
}'''
anime_sama_routes = r.extract_routes(anime_sama)
assert "/template-php/defaut/fetch.php" in anime_sama_routes, anime_sama_routes
assert any("/catalogue/" in x and "episodes.js" in x for x in anime_sama_routes), anime_sama_routes
anime_sama_contracts = r.recognize_request_contracts(anime_sama, anime_sama_routes)
assert any(x.get("role") == "search" and x.get("method") == "POST" for x in anime_sama_contracts), anime_sama_contracts
assert r.infer_family(anime_sama, anime_sama_routes, anime_sama_contracts) == "catalogue-episodes-js"


# Yoru template interface by itself describes shape, not executable provider paths.
yoru_template = r'''
export async function getStreams(tmdbId, mediaType, season, episode) {
  const metadata = await getTmdbMetadata(tmdbId, mediaType);
  return extractStreams(metadata, season, episode);
}
async function request(url, options) { return fetch(url, options); }
'''
assert r.extract_routes(yoru_template) == [], r.extract_routes(yoru_template)


# DLE/Frenchstream-style form search, seasons/episodes and dynamic player API.
frenchstream = r'''
const BASE = "https://example.invalid";
async function search(query) {
  return fetchText(BASE + '/index.php?do=search&subaction=search&story=' + encodeURIComponent(query), {
    method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded','Referer':BASE},
    body:'do=search&subaction=search&story='+encodeURIComponent(query)
  });
}
async function seasons(id) { return fetchText(BASE + '/engine/ajax/controller.php?mod=season&news_id=' + id); }
async function episodes(id, season) { return fetchText(BASE + '/engine/ajax/controller.php?mod=episode&news_id=' + id + '&season=' + season); }
async function player(id) { return fetchText(BASE + '/engine/ajax/controller.php?mod=playepisode&news_id=' + id); }
'''
french_routes = r.extract_routes(frenchstream)
assert any("story={query}" in x for x in french_routes), french_routes
assert any("controller.php?mod=playepisode" in x for x in french_routes), french_routes
french_contracts = r.recognize_request_contracts(frenchstream, french_routes)
assert any(x.get("method") == "POST" and x.get("role") == "search" for x in french_contracts), french_contracts


# Kehflix-like title -> player -> streams chain.
kehflix = r'''
const BASE='https://kehflix.example';
async function a(id){return fetchJson(`${BASE}/title/${id}`)}
async function b(id){return fetchText(`${BASE}/player/${id}`)}
async function c(id){return fetchJson(`${BASE}/api/streams/${id}`)}
'''
keh_routes = r.extract_routes(kehflix)
assert any(x.startswith('/title/') for x in keh_routes), keh_routes
assert any(x.startswith('/player/') for x in keh_routes), keh_routes
assert any('/api/streams/' in x for x in keh_routes), keh_routes
keh_contracts = r.recognize_request_contracts(kehflix, keh_routes)
assert any(x.get('role') == 'player' for x in keh_contracts), keh_contracts
assert any(x.get('role') == 'api' for x in keh_contracts), keh_contracts


# Minified AIO-style bundle; literal junk must not survive.
aio = "const b='https://x.invalid';async function g(q){return fetch(b+'/api/search?q='+encodeURIComponent(q)).then(x=>x.json())}async function p(id){return fetch(b+'/player/'+id).then(x=>x.text())};const z='/wp-json/oembed';const a='/resolvers.js';"
aio_routes = r.extract_routes(aio)
assert any('/api/search?q={query}' == x for x in aio_routes), aio_routes
assert any('/player/{id}' == x for x in aio_routes), aio_routes
assert '/wp-json/oembed' not in aio_routes, aio_routes
assert '/resolvers.js' not in aio_routes, aio_routes


# AnimeKai: concatenated search and episode expressions. HTML data attributes are
# extraction evidence, never routes.
animekai = r'''
const ANIKAI_BASE='https://www3.anikai.cc';
async function searchAnikai(query) {
  const endpoint = ANIKAI_BASE + '/browser?keyword=' + encodeURIComponent(query);
  return fetchText(endpoint);
}
async function getEpisode(result, episode) {
  const endpoint = result.url + '/ep-' + episode;
  return fetchText(endpoint);
}
function read(html){return /data-video=["']([^"']+)/.exec(html)}
'''
animekai_routes = r.extract_routes(animekai)
assert "/browser?keyword={query}" in animekai_routes, animekai_routes
assert "/ep-{episode}" in animekai_routes, animekai_routes
assert "/data-video=" not in animekai_routes, animekai_routes
animekai_contracts = r.recognize_request_contracts(animekai, animekai_routes)
assert any(
    row.get("route") == "/browser?keyword={query}"
    and row.get("executedEvidence") is True
    for row in animekai_contracts
), animekai_contracts
assert any(
    row.get("route") == "/ep-{episode}"
    and row.get("executedEvidence") is True
    for row in animekai_contracts
), animekai_contracts


# AnimeZey-like worker search: host is dynamic but API path, POST JSON, body fields
# and Referer remain statically provable.
animezey = r'''
async function _postSearch(workerDomain, payload) {
  const url = 'https://' + workerDomain + '/1:search';
  return fetchPlain(url, {
    method:'POST',
    headers:{'content-type':'application/json','Referer':url},
    body:JSON.stringify(payload)
  });
}
async function _searchEpisodes(query){return _postSearch('x.workers.dev',{q:query,page_token:null,page_index:0})}
async function _searchMovies(query){return _postSearch('x.workers.dev',{q:query})}
async function _extractPlayerUrl(workerDomain,itemPath){const endpoint='https://'+workerDomain+itemPath+'?a=view';return fetchText(endpoint,{headers:{Referer:endpoint}})}
'''
animezey_routes = r.extract_routes(animezey)
assert "/1:search" in animezey_routes, animezey_routes
animezey_contracts = r.recognize_request_contracts(animezey, animezey_routes)
search_contract = next((x for x in animezey_contracts if x.get("route") == "/1:search"), None)
assert search_contract, animezey_contracts
assert search_contract.get("method") == "POST", search_contract
assert search_contract.get("jsonEncoded") is True, search_contract
assert search_contract.get("refererRequired") is True, search_contract


# Repeated local variable names in separate functions must resolve at each call
# site rather than leaking the later assignment into the earlier route.
anime_ultime_scope = r'''
const BASE='https://anime-ultime.example';
async function search(query){const endpoint=BASE+'/search?q='+encodeURIComponent(query);return fetchText(endpoint)}
async function player(id){const endpoint=BASE+'/VideoPlayer.html?id='+id;return fetchText(endpoint)}
'''
ultime_routes = r.extract_routes(anime_ultime_scope)
assert "/search?q={query}" in ultime_routes, ultime_routes
assert "/VideoPlayer.html?id={id}" in ultime_routes, ultime_routes
ultime_contracts = r.recognize_request_contracts(anime_ultime_scope, ultime_routes)
assert all(
    any(row.get("route") == expected and row.get("executedEvidence") is True for row in ultime_contracts)
    for expected in ("/search?q={query}", "/VideoPlayer.html?id={id}")
), ultime_contracts

print("Provider contract recognizer tests passed: guarded normalization, scoped expressions, request roles, no upstream JS execution")
