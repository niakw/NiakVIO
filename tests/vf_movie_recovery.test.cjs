#!/usr/bin/env node
const assert = require('node:assert/strict');
const path = require('node:path');
const manifest = require('../manifest.json');

const targets = ['streamzo', 'movix', 'frenchstream', 'coflix', 'flemmix'];
const fixtures = [
  { id: '157336', title: 'Interstellar', year: 2014, slug: 'interstellar' },
  { id: '447365', title: 'Les Gardiens de la Galaxie : Volume 3', year: 2023, slug: 'les-gardiens-de-la-galaxie-volume-3' },
];
const entries = Object.fromEntries(manifest.scrapers.map((row) => [String(row.id).toLowerCase(), row]));
const externalPlayer = 'https://player.example/embed/movie';
const provenHls = 'https://s1.fsvid.lol/troll/master.m3u8';
const tvFixture = { id: '94605', title: 'Arcane', year: 2021, slug: 'arcane', season: 1, episode: 1 };

function fixtureForId(id) {
  if (String(id) === tvFixture.id) return tvFixture;
  return fixtures.find((row) => row.id === String(id)) || fixtures[0];
}
function tmdbResponse(url) {
  const parsed = new URL(url);
  const id = parsed.pathname.split('/').filter(Boolean).at(-1);
  const fixture = fixtureForId(id);
  return new Response(JSON.stringify({
    id: Number(fixture.id),
    title: fixture.title,
    name: fixture.title,
    original_title: fixture.title,
    original_name: fixture.title,
    release_date: `${fixture.year}-05-01`,
    first_air_date: `${fixture.year}-05-01`,
  }), { status: 200, headers: { 'content-type': 'application/json' } });
}
function fixtureForUrl(url) {
  const decoded = decodeURIComponent(url.toString()).toLowerCase();
  if (decoded.includes(tvFixture.slug) || decoded.includes(tvFixture.title.toLowerCase())) return tvFixture;
  return fixtures.find((row) => decoded.includes(row.slug) || decoded.includes(row.title.toLowerCase())) || fixtures[0];
}
function dleSearch(base, fixture) {
  return `<!doctype html><div class="short"><a href="${base}/films/123-${fixture.slug}-streaming-complet.html"><div class="short-title">${fixture.title}</div></a></div>`;
}
function detailPage(fixture) {
  if (fixture.id === tvFixture.id) return `<!doctype html><h1>${fixture.title}</h1><button data-season="1" data-episode="1" data-lang="vf" data-src="https://player.example/embed/tv/${fixture.id}/1/1"></button>`;
  return `<!doctype html><h1>${fixture.title}</h1><section id="player" data-embed="${externalPlayer}/${fixture.id}"></section>`;
}
function hlsBody() {
  return '\uFEFF  #EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:10\n#EXTINF:10.0,\nsegment-1.ts\n#EXTINF:10.0,\nsegment-2.ts\n#EXT-X-ENDLIST\n';
}

global.fetch = async (input) => {
  const raw = typeof input === 'string' ? input : input.url;
  const url = new URL(raw);
  if (url.hostname === 'api.themoviedb.org') return tmdbResponse(raw);
  if (url.hostname === 'movix.fun' && url.pathname === '/') {
    return new Response('<script src="/assets/app.js"></script>', { status: 200, headers: { 'content-type': 'text/html' } });
  }
  if (url.hostname === 'movix.fun' && url.pathname === '/assets/app.js') {
    return new Response('const movie="/api/catalog/movie/{id}"; const tv="/api/catalog/tv/{id}/season/{season}";', { status: 200, headers: { 'content-type': 'application/javascript' } });
  }
  if (url.hostname === 'api.movix.fun' && url.pathname.startsWith('/api/catalog/movie/')) {
    const fixture = fixtureForId(url.pathname.split('/').filter(Boolean).at(-1));
    return new Response(JSON.stringify({
      success: true,
      players: {
        VFF: [{ url: `https://vidzy.example/embed-${fixture.id}.html` }],
        Default: [{ url: 'https://fstream.top/troll/master.m3u8' }],
      },
    }), { status: 200, headers: { 'content-type': 'application/json' } });
  }
  if (url.hostname === 'api.movix.fun' && url.pathname.startsWith('/api/catalog/tv/')) {
    return new Response(JSON.stringify({
      success: true,
      episodes: {
        '1': { languages: { vf: [{ url: `https://player.example/embed/tv/${tvFixture.id}/1/1` }] } },
      },
    }), { status: 200, headers: { 'content-type': 'application/json' } });
  }
  if (url.hostname === 's1.fsvid.lol' && url.pathname === '/troll/master.m3u8') {
    return new Response(hlsBody(), { status: 200, headers: { 'content-type': 'text/plain; charset=utf-8' } });
  }
  if (['vidzy.example', 'player.example'].includes(url.hostname)) {
    return new Response(`<html><script>const file=${JSON.stringify(provenHls)};</script></html>`, { status: 200, headers: { 'content-type': 'text/html' } });
  }
  const fixture = fixtureForUrl(url);
  if (url.hostname === 'streamzo.fr') {
    return new Response(detailPage(fixture), { status: 200, headers: { 'content-type': 'text/html' } });
  }
  if (['fs16.lol', 'coflix.esq', 'flemmix.men'].includes(url.hostname)) {
    if (/\/films?\/|interstellar|gardiens|arcane/.test(url.pathname) && !/index\.php/.test(url.pathname)) {
      return new Response(detailPage(fixture), { status: 200, headers: { 'content-type': 'text/html' } });
    }
    return new Response(dleSearch(url.origin, fixture), { status: 200, headers: { 'content-type': 'text/html' } });
  }
  return new Response('not found', { status: 404, headers: { 'content-type': 'text/plain' } });
};

function assertSafeRows(id, fixtureId, rows, kind) {
  assert(Array.isArray(rows) && rows.length > 0, `${id}/${fixtureId}: ${kind} recovery produced no player`);
  assert(rows.every((row) => typeof row.url === 'string' && /^https?:\/\//.test(row.url)), `${id}/${fixtureId}: invalid ${kind} player URL`);
  assert(rows.every((row) => !/fstream\.top/i.test(row.url)), `${id}/${fixtureId}: known fake short player escaped filtering`);
  assert(rows.every((row) => !/(?:^|\.)(?:snap\.com|snapchat\.com|ctfassets\.net|sc-cdn\.net)$/i.test(new URL(row.url).hostname)), `${id}/${fixtureId}: unrelated advertising media escaped filtering`);
}

(async () => {
  for (const id of targets) {
    const entry = entries[id];
    assert(entry, `missing manifest entry: ${id}`);
    const providerPath = path.resolve(__dirname, '..', entry.filename);
    delete require.cache[require.resolve(providerPath)];
    const provider = require(providerPath);
    for (const fixture of fixtures) {
      const rows = await provider.getStreams(fixture.id, 'movie', null, null, {});
      assertSafeRows(id, fixture.id, rows, 'movie');
    }
    if (id === 'flemmix') continue;
    const tvRows = await provider.getStreams(tvFixture.id, 'tv', tvFixture.season, tvFixture.episode, {});
    assertSafeRows(id, tvFixture.id, tvRows, 'TV');
  }
  console.log('VF catalogue recovery tests passed with content-proven HLS (Interstellar + Guardians Vol. 3 + Arcane S01E01)');
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
