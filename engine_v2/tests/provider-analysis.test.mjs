import assert from "node:assert/strict";
import { analyzeProviderCode, mergeProviderKnowledge } from "../src/provider-analysis.mjs";

const code = `
const axios = require('axios');
const cheerio = require('cheerio');
async function getStreams(tmdbId, mediaType, season, episode) {
  const base = 'https://example.test';
  const search = await fetch(base + '/api/search?q=' + tmdbId, {
    headers: { 'Referer': base + '/', 'Origin': base, 'Cookie': SCRAPER_SETTINGS.cookie }
  });
  const player = base + '/embed/player';
  const media = 'https://cdn.example.test/master.m3u8';
  return [{ title: 'x', url: media }];
}
module.exports = { getStreams, onSettings: async () => [] };
`;

const analysis = analyzeProviderCode(code);
assert.equal(analysis.exports.getStreams, true);
assert.equal(analysis.exports.moduleExports, true);
assert.equal(analysis.exports.onSettings, true);
assert.ok(analysis.hosts.includes('example.test'));
assert.ok(analysis.hosts.includes('cdn.example.test'));
assert.ok(analysis.routeHints.some((route) => route.includes('/api/search')));
assert.equal(analysis.headers.referer, true);
assert.equal(analysis.headers.origin, true);
assert.equal(analysis.headers.cookie, true);
assert.equal(analysis.settings.readsScraperSettings, true);
assert.ok(analysis.mediaFormats.includes('m3u8'));
assert.equal(analysis.stages.search, true);
assert.equal(analysis.stages.episode, true);
assert.equal(analysis.stages.player, true);
assert.equal(analysis.strategyKind, 'hybrid');

const merged = mergeProviderKnowledge({
  id: 'example',
  supportedTypes: ['movie', 'tv'],
  languages: ['fr'],
  formats: [],
  hasSettings: false,
}, [{ source: { upstreamId: 'a' }, analysis, error: null }]);
assert.equal(merged.id, 'example');
assert.equal(merged.requiresSettings, true);
assert.ok(merged.hosts.includes('example.test'));
assert.equal(merged.state, 'knowledge-seeded');

console.log('engine v2 provider analysis tests passed');
