#!/usr/bin/env node
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {
  inferSupportedTypes,
  isAnimeFocusedCatalogue,
} = require('../scripts/provider_semantics.cjs');

const hianime = {
  canonical_id: 'hianime',
  metadata: {
    id: 'HIANIME',
    name: 'HiAnime',
    description: 'Anime catalogue',
    supportedTypes: ['anime', 'tv', 'series'],
    canonicalSupportedTypes: ['anime'],
  },
};
assert.deepEqual(inferSupportedTypes(hianime), ['anime']);
assert.equal(isAnimeFocusedCatalogue(hianime), true);

const animeSama = {
  canonical_id: 'anime-sama',
  metadata: {
    id: 'anime-sama',
    name: 'Anime-Sama',
    description: 'Anime catalogue',
    supportedTypes: ['movie', 'anime', 'tv', 'series'],
    canonicalSupportedTypes: ['movie', 'anime'],
  },
};
assert.deepEqual(inferSupportedTypes(animeSama), ['movie', 'anime']);
assert.equal(isAnimeFocusedCatalogue(animeSama), true);

const castle = {
  canonical_id: 'castle',
  metadata: {
    id: 'CASTLE',
    name: 'Castle',
    supportedTypes: ['movie', 'tv'],
  },
};
assert.deepEqual(inferSupportedTypes(castle), ['movie', 'tv']);

const mixed = {
  canonical_id: 'mixed',
  metadata: {
    id: 'mixed',
    name: 'Mixed',
    description: 'Movies, TV series and anime',
    supportedTypes: ['movie', 'tv', 'anime'],
    canonicalSupportedTypes: ['movie', 'tv', 'anime'],
  },
};
assert.deepEqual(inferSupportedTypes(mixed), ['movie', 'tv', 'anime']);

// Current published metadata is an authoritative oracle for the fixture
// category. The preceding availability run falsely sampled Breaking Bad on
// AnimeKai/Anime-Ultime despite their canonical anime-only declarations.
const manifest = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'manifest.json'), 'utf8'));
const canonicalRows = manifest.scrapers.filter(row =>
  Array.isArray(row.canonicalSupportedTypes) && row.canonicalSupportedTypes.length > 0);
assert.ok(canonicalRows.length >= 10, 'missing current canonical catalogue test cohort');
for (const row of canonicalRows) {
  const candidate = { canonical_id: String(row.id).toLowerCase(), metadata: row };
  const expected = ['movie', 'tv', 'anime'].filter(type => row.canonicalSupportedTypes.includes(type));
  assert.deepEqual(inferSupportedTypes(candidate), expected,
    'manifest catalogue semantic mismatch: ' + row.id);
}
for (const id of ['animekai', 'anime-ultime']) {
  const row = canonicalRows.find(item => String(item.id).toLowerCase() === id);
  assert.ok(row, 'missing published source ' + id);
  assert.deepEqual(inferSupportedTypes({
    canonical_id: id, metadata: row,
  }), ['anime'], id + ' cannot receive a generic TV fixture');
}

// A trusted live variant may enrich canonical types. A local published
// baseline alone cannot widen a source; descriptions/aliases never widen
// an explicit current declaration, even if they mention TV and movies.
const declared = {
  canonical_id: 'catalogue-example',
  source: 'active-upstream',
  metadata: { description: 'TV, films and anime', supportedTypes: ['movie', 'tv', 'anime'],
              canonicalSupportedTypes: ['anime'] },
};
assert.deepEqual(inferSupportedTypes(declared), ['anime']);
assert.deepEqual(inferSupportedTypes({
  ...declared,
  canonical_metadata: { sources: ['published-baseline'], canonicalSupportedTypes: ['tv'] },
}), ['anime']);
assert.deepEqual(inferSupportedTypes({
  ...declared,
  canonical_metadata: { sources: ['independent-live-variant'], canonicalSupportedTypes: ['tv'] },
}), ['tv', 'anime']);

console.log('provider semantic/transport fixture inference tests passed (current manifest + live source authority)');
