const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const ROOT = path.resolve(__dirname, '..');
const WORKER = path.join(ROOT, 'scripts', 'provider_worker.cjs');
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'niakvio-worker-identity-'));
const fixture = JSON.stringify({tmdbId:'95479',mediaType:'anime',category:'anime',title:'Jujutsu Kaisen',season:1,episode:1});
const context = JSON.stringify({locale:'fr-FR',platform:'android',maxSettingsProfiles:1});

function run(markers, stream) {
  const provider = path.join(dir, 'provider-' + Math.random().toString(16).slice(2) + '.cjs');
  const source = markers + '\nmodule.exports={getStreams:async()=>[' + JSON.stringify(stream) + ']};\n';
  fs.writeFileSync(provider, source);
  const result = spawnSync(process.execPath,[WORKER,provider,fixture,context],{cwd:ROOT,encoding:'utf8',timeout:15000});
  assert.equal(result.status,0,result.stderr || result.stdout);
  const line=result.stdout.split(/\r?\n/).find((x)=>x.startsWith('NUVIO_HEALTH_RESULT='));
  assert.ok(line,result.stdout);
  return JSON.parse(line.slice('NUVIO_HEALTH_RESULT='.length));
}

const sourceCoordinate={name:'Managed identity',title:'Mugiwara',url:'https://media.example/master.m3u8',niakvioIdentityAuthority:'provider-source-coordinate-v1',niakvioIdentitySourceTitle:'Jujutsu Kaisen',niakvioIdentityMediaType:'anime',niakvioIdentitySeason:1,niakvioIdentityEpisode:1,niakvioPresentationOnly:true};
const mugiMarkers='/* STARTFIX:PROVIDER.MUGIWARASTREAM.PACKED.RUNTIME.V1 */\n/* NIAKVIO_MUGIWARASTREAM_PACKED_RUNTIME_V1 */';
const managed=run(mugiMarkers,sourceCoordinate);
assert.equal(managed.streams.length,1);
assert.equal(managed.streams[0].niakvioIdentityAuthority,'provider-source-coordinate-v1');
assert.equal(managed.streams[0].niakvioIdentitySourceTitle,'Jujutsu Kaisen');
assert.equal(managed.streams[0].niakvioIdentityMediaType,'anime');
assert.equal(managed.streams[0].niakvioIdentitySeason,1);
assert.equal(managed.streams[0].niakvioIdentityEpisode,1);
assert.equal(managed.streams[0].niakvioPresentationOnly,true);

const spoofed=run('',sourceCoordinate);
for(const key of ['niakvioIdentityAuthority','niakvioIdentitySourceTitle','niakvioIdentityMediaType','niakvioIdentitySeason','niakvioIdentityEpisode','niakvioPresentationOnly']) assert.equal(Object.hasOwn(spoofed.streams[0],key),false,key);
const malformed=run(mugiMarkers,{...sourceCoordinate,niakvioIdentityEpisode:0});
assert.equal(Object.hasOwn(malformed.streams[0],'niakvioIdentityAuthority'),false);

const directMarkers='/* STARTFIX:PROVIDER.GENERIC.TICKETED_ENCRYPTED.API.V1 */\n/* NIAKVIO_TICKETED_ENCRYPTED_API_RUNTIME_V1 */';
const direct=run(directMarkers,{url:'https://media.example/movie.m3u8',niakvioIdentityAuthority:'tmdb-direct-route-v1',niakvioIdentityTmdbId:'95479',niakvioIdentityMediaType:'anime',niakvioIdentitySeason:1,niakvioIdentityEpisode:1,niakvioPresentationOnly:true});
assert.equal(direct.streams[0].niakvioIdentityAuthority,'tmdb-direct-route-v1');
assert.equal(direct.streams[0].niakvioIdentityTmdbId,'95479');

fs.rmSync(dir,{recursive:true,force:true});
console.log('provider worker managed identity provenance contract passed');
