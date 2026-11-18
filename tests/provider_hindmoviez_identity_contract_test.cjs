#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { streamIdentity } = require('../scripts/nuvio_client_lab.cjs');

const root = path.resolve(__dirname, '..');
const patch = fs.readFileSync(path.join(root, 'scripts/provider_patches/hindmoviez_runtime_v1.py'), 'utf8');
if (!patch.includes('title:f,filename:f,sourceName:f')) {
  throw new Error('HindMoviez runtime must preserve provider filename identity');
}
if (/season\s*:\s*Number\([^\n;]*\)\s*\|\|\s*1/.test(patch)) {
  throw new Error('HindMoviez runtime must not collapse S00 to S01 through JavaScript truthiness');
}
if (!patch.includes('season:C((o&&o.season)!=null?o.season:(a[2]!=null?a[2]:x.season),1,true)')) {
  throw new Error('HindMoviez runtime must preserve season zero at its request boundary');
}
if (!patch.includes('episode:C((o&&o.episode)!=null?o.episode:(a[3]!=null?a[3]:x.episode),1,false)')) {
  throw new Error('HindMoviez runtime must keep episode coordinates positive');
}

const movieFile = 'The.Colony.AKA.Tides.2021.480p.BluRay.Hindi.English.Esubs.mkv';
const movie = streamIdentity({
  name: 'HindMoviez | 480p',
  title: movieFile,
  filename: movieFile,
  sourceName: movieFile,
  url: 'https://opaque.example.workers.dev/?file=opaque',
  provider: 'hindmoviez',
}, {
  mediaType: 'movie',
  title: 'The Colony',
  aliases: ['The Colony', 'Colony', 'Tides'],
  year: 2021,
});
if (movie.status !== 'match') throw new Error('movie identity not preserved: ' + JSON.stringify(movie));

const tvFile = 'Breaking.Bad.S01E01.1080p.WEB-DL.mkv';
const tv = streamIdentity({
  name: 'HindMoviez | 1080p',
  title: tvFile,
  filename: tvFile,
  sourceName: tvFile,
  url: 'https://opaque.example.workers.dev/?file=opaque',
  provider: 'hindmoviez',
}, {
  mediaType: 'tv',
  title: 'Breaking Bad',
  season: 1,
  episode: 1,
});
if (tv.status !== 'match') throw new Error('tv identity regressed: ' + JSON.stringify(tv));

console.log('HindMoviez stream identity contract passed');
