import test from 'node:test';
import assert from 'node:assert/strict';
import { allowedChannels, builder, getBlockReason, manifest, selectCatalog } from './server.js';

const addon = builder.getInterface();

test('manifest exposes multiple Nuvio catalogs', () => {
  const ids = manifest.catalogs.map((catalog) => catalog.id);
  assert.deepEqual(ids, [
    'official-tv-all',
    'official-tv-information',
    'official-tv-culture',
    'official-tv-generaliste'
  ]);
});

test('all configured channels pass the blacklist policy', () => {
  assert.ok(allowedChannels.length > 0);
  for (const channel of allowedChannels) assert.equal(getBlockReason(channel), null);
});

test('blocked host, blocked name and unverified channel are rejected', () => {
  assert.equal(
    getBlockReason({
      id: 'fake',
      name: 'Chaîne test',
      verified: true,
      officialPage: 'https://fstv.rest/channel/test'
    }),
    'blocked-host'
  );
  assert.equal(
    getBlockReason({
      id: 'fake-bein',
      name: 'beIN Sports 42',
      verified: true,
      officialPage: 'https://example.org/live'
    }),
    'blocked-name'
  );
  assert.equal(
    getBlockReason({
      id: 'unverified',
      name: 'Chaîne inconnue',
      officialPage: 'https://example.org/live'
    }),
    'unverified'
  );
});

test('category catalogs only expose matching channels', () => {
  assert.ok(selectCatalog('official-tv-information').every((item) => item.category === 'Information'));
  assert.ok(selectCatalog('official-tv-culture').every((item) => item.category === 'Culture'));
  assert.ok(selectCatalog('official-tv-generaliste').every((item) => item.category === 'Généraliste'));
});

test('search works across the complete catalog', () => {
  const results = selectCatalog('official-tv-all', 'arte');
  assert.equal(results.length, 1);
  assert.equal(results[0].id, 'arte-fr');
});

test('addon interface returns catalog, meta and stream responses', async () => {
  const catalog = await addon.get({ resource: 'catalog', type: 'tv', id: 'official-tv-all', extra: {} });
  assert.equal(catalog.metas.length, allowedChannels.length);

  const first = allowedChannels[0];
  const meta = await addon.get({ resource: 'meta', type: 'tv', id: `niakvio-tv:${first.id}`, extra: {} });
  assert.equal(meta.meta.id, `niakvio-tv:${first.id}`);
  assert.equal(meta.meta.videos.length, 1);

  const stream = await addon.get({
    resource: 'stream',
    type: 'tv',
    id: `niakvio-tv:${first.id}:live`,
    extra: {}
  });
  assert.equal(stream.streams.length, 1);
  assert.ok(stream.streams[0].url || stream.streams[0].externalUrl);
});
