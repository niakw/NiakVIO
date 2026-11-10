#!/usr/bin/env node
// The real published category/fixture roster is the authority. These tests
// cover the *harness decision*, not provider success or decoded playback.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { shouldRetryNoRequest } = require('../scripts/availability_fallback_policy.cjs');
const { inferSupportedTypes } = require('../scripts/provider_semantics.cjs');
const config = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'health-config.json')));
const manifest = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'manifest.json')));
const sample = category => ({
  status: 'provider_unreachable',
  failure_class: 'no_provider_request_observed',
  fixture: { ...config.fixtures[category][0], category },
  runtime_errors: [],
});
for (const category of ['movie', 'tv', 'anime']) {
  const titles = config.fixtures[category];
  assert.ok(titles.length >= 2, 'availability needs independent real titles for '+category);
  const ids = new Set(titles.slice(0, 2).map(row => String(row.tmdbId)));
  assert.equal(ids.size, 2, 'alternate must be a distinct current TMDB title');
  assert.equal(shouldRetryNoRequest([sample(category)], category), true);
  for (const status of ['healthy','blocked','unavailable','no_streams','runtime_error']) {
    assert.equal(shouldRetryNoRequest([{...sample(category),status}],category),false);
  }
  assert.equal(shouldRetryNoRequest([{...sample(category),runtime_errors:[{code:'x'}]}],category),false);
  assert.equal(shouldRetryNoRequest([sample(category),{...sample(category),status:'blocked'}],category),false);
  assert.equal(shouldRetryNoRequest([sample(category)],category==='anime'?'tv':'anime'),false);
}
for (const id of ['animekai','anime-ultime']) {
  const row = manifest.scrapers.find(x=>String(x.id).toLowerCase()===id);
  assert.ok(row);
  assert.deepEqual(inferSupportedTypes({canonical_id:id,metadata:row}),['anime']);
  assert.equal(shouldRetryNoRequest([sample('anime')], 'anime'),true);
  assert.equal(shouldRetryNoRequest([sample('anime')], 'tv'),false);
}
console.log('AVAILABILITY_NO_REQUEST_SECOND_WORK_OK one_extra_same_canonical_category=true playback_not_proven=true');
