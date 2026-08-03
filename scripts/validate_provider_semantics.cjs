#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-only
'use strict';

const assert = require('node:assert/strict');
const { inferSupportedTypes, roundRobin } = require('./provider_semantics.cjs');

const movix = {
  canonical_id: 'movix',
  metadata: {
    id: 'movix',
    name: 'Movix',
    description: 'Films, Séries et Animes en VF et VOSTFR.',
    supportedTypes: ['anime'],
  },
};
assert.deepEqual(
  inferSupportedTypes(movix),
  ['movie', 'tv', 'anime'],
  'Movix must remain available for films, series and anime',
);

const incompleteMovixVariant = {
  canonical_id: 'movix',
  metadata: {
    id: 'movix',
    description: 'Animes en VF et VOSTFR',
    supportedTypes: ['anime'],
  },
  canonical_metadata: {
    descriptions: ['Films, Séries et Animes en VF et VOSTFR.'],
    supportedTypes: ['anime'],
  },
};
assert.deepEqual(
  inferSupportedTypes(incompleteMovixVariant),
  ['movie', 'tv', 'anime'],
  'canonical descriptions from the other manifests must restore Movix movie/TV coverage',
);

const animeOnly = {
  canonical_id: 'anime-only',
  metadata: {
    description: 'Animes et mangas en streaming',
    supportedTypes: ['movie', 'tv'],
  },
};
assert.deepEqual(
  inferSupportedTypes(animeOnly),
  ['movie', 'anime'],
  'anime catalogues must expose anime films without being presented as general TV catalogues',
);

const pool = roundRobin([
  [{ category: 'movie', id: 1 }],
  [{ category: 'tv', id: 2 }],
  [{ category: 'anime', id: 3 }],
]);
assert.deepEqual(
  pool.map((item) => item.category),
  ['movie', 'tv', 'anime'],
  'multi-catalogue representative tests must begin with a movie, then TV, then anime',
);

console.log('Provider semantics self-test passed: Movix movie/TV/anime coverage and representative fixture order are preserved.');
