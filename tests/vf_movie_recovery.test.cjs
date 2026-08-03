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

function fixtureForId(id) {
  return fixtures.find((row) => row.id === String(id)) || fixtures[0];
}
function tmdbResponse(url) {
  const parsed = new URL(url);
  const id = parsed.pathname.split('/').filter(Boolean).at(-1);
  const fixture = fixtureForId(id);
  return new Response(JSON.stringify({
    id: Number(fixture.id),
    title: fixture.title,
    original_title: fixture.title,
    release_date: `${fixture.year}-05-01`,
  }), { status: 200, headers: { 'content-type': 'application/json' } });
}
function fixtureForUrl(url) {
  const decoded = decodeURIComponent(url.toString()).toLowerCase();
  return fixtures.find((row) => decoded.includes(row.slug) || decoded.includes(row.title.toLowerCase())) || fixtures[0];
}
function dleSearch(base, fixture) {
  return `<!doctype html><div class="short"><a href="${base}/films/123-${fixture.slug}-streaming-complet.html"><div class="short-title">${fixture.title}</div></a></div>`;
}
function detailPage(fixture) {
  return `<!doctype html><h1>${fixture.title}</h1><section id="player" data-embed="${externalPlayer}/${fixture.id}"></section>`;
}

global.fetch = async (input) => {
  const raw = typeof input === 'string' ? input : input.url;
  const url = new URL(raw);
  if (url.hostname === 'api.themoviedb.org') return tmdbResponse(raw);
  if (url.hostname === 'api.movix.fun') {
    const fixture = fixtureForId(url.pathname.split('/').filter(Boolean).at(-1));
    return new Response(JSON.stringify({
      success: true,
      players: {
        VFF: [{ url: `https://vidzy.example/embed-${fixture.id}.html` }],
        Default: [{ url: 'https://fstream.top/troll/master.m3u8' }],
      },
    }), { status: 200, headers: { 'content-type': 'application/json' } });
  }
  if (['vidzy.example', 'player.example'].includes(url.hostname)) {
    return new Response('<html>external player</html>', { status: 200, headers: { 'content-type': 'text/html' } });
  }
  const fixture = fixtureForUrl(url);
  if (url.hostname === 'streamzo.fr') {
    return new Response(detailPage(fixture), { status: 200, headers: { 'content-type': 'text/html' } });
  }
  if (['fs16.lol', 'coflix.esq', 'flemmix.men'].includes(url.hostname)) {
    if (/\/films?\/|interstellar|gardiens/.test(url.pathname) && !/index\.php/.test(url.pathname)) {
      return new Response(detailPage(fixture), { status: 200, headers: { 'content-type': 'text/html' } });
    }
    return new Response(dleSearch(url.origin, fixture), { status: 200, headers: { 'content-type': 'text/html' } });
  }
  return new Response('not found', { status: 404, headers: { 'content-type': 'text/plain' } });
};

(async () => {
  for (const id of targets) {
    const entry = entries[id];
    assert(entry, `missing manifest entry: ${id}`);
    const providerPath = path.resolve(__dirname, '..', entry.filename);
    delete require.cache[require.resolve(providerPath)];
    const provider = require(providerPath);
    for (const fixture of fixtures) {
      const rows = await provider.getStreams(fixture.id, 'movie', null, null, {});
      assert(Array.isArray(rows) && rows.length > 0, `${id}/${fixture.id}: movie recovery produced no player`);
      assert(rows.every((row) => typeof row.url === 'string' && /^https?:\/\//.test(row.url)), `${id}/${fixture.id}: invalid player URL`);
      assert(rows.every((row) => !/fstream\.top|\/troll\//i.test(row.url)), `${id}/${fixture.id}: fake short player escaped filtering`);
    }
  }
  console.log('VF movie recovery tests passed (Interstellar + Guardians Vol. 3)');
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
