#!/usr/bin/env node
'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {
  WINDOWS_UA,
  buildWorkerContext,
  classify,
  executionGroups,
  mapLimit,
  parseWorkerOutput,
  resolveProvider,
  summarizeStream,
  summarizePolicy,
  streamIdentity,
  tailText,
  verifyRuntimeContract,
} = require('../scripts/nuvio_client_lab.cjs');

const repositoryRoot = path.resolve(__dirname, '..');
const packageJson = JSON.parse(fs.readFileSync(path.join(repositoryRoot, 'package.json'), 'utf8'));
const labWorkflow = fs.readFileSync(path.join(repositoryRoot, '.github/workflows/nuvio-client-lab.yml'), 'utf8');
const npmTestLifecycle = `${packageJson.scripts.pretest || ''} ${packageJson.scripts.test || ''}`;
assert.match(npmTestLifecycle, /node tests\/nuvio_client_lab\.test\.cjs/);
assert.match(packageJson.scripts.posttest || '', /python3 scripts\/validate_release_integrity\.py/);
for (const requiredPath of [
  'manifest.json',
  'vf/manifest.json',
  'provider-overrides.json',
  'providers/**',
  'scripts/nuvio_client_lab.cjs',
  'scripts/provider_worker.cjs',
  'scripts/provider_patches/**',
  'tests/nuvio_client_lab.test.cjs',
]) {
  assert.equal(labWorkflow.includes(`- "${requiredPath}"`), true, `lab workflow must watch ${requiredPath}`);
}
assert.match(labWorkflow, /python3 scripts\/validate_release_integrity\.py/);
assert.doesNotMatch(labWorkflow, /lab\/nuvio-client-matrix/);

const manifest = {
  scrapers: [
    { id: 'FLEMMIX', name: 'Flemmix', filename: 'providers/flemmix.js' },
    { id: 'MOVIX', name: 'Movix', filename: 'providers/movix.js' },
  ],
};
assert.equal(resolveProvider(manifest, 'flemmix').filename, 'providers/flemmix.js');
assert.equal(resolveProvider(manifest, 'Movix').id, 'MOVIX');
assert.throws(() => resolveProvider(manifest, 'missing'), /provider not found/);

assert.deepEqual(executionGroups(['tv', 'desktop', 'mobile']), [
  { runtimeGroup: 'tv', clients: ['tv'] },
  { runtimeGroup: 'compose', clients: ['desktop', 'mobile'] },
]);

const context = buildWorkerContext('tv', { tmdbId: '157336', mediaType: 'movie' }, {});
assert.equal(context.userAgent, WINDOWS_UA);
assert.equal(context.injectAcceptLanguage, false);
assert.equal(context.clientRuntimeLab.invocationContract, 'positional-compatible');

const parsed = parseWorkerOutput('noise\nNUVIO_HEALTH_RESULT={"ok":true,"stream_count":1,"streams":[]}\n');
assert.equal(parsed.ok, true);
assert.equal(parsed.stream_count, 1);
assert.equal(tailText('abcdefgh', 'ijkl', 6), 'ghijkl');

const summary = summarizeStream({
  url: 'https://cdn.example/video.m3u8?token=secret',
  title: '1080p',
  headers: { Referer: 'https://example.test/', Authorization: 'secret' },
  subtitles: [{ url: 'https://sub.example/a.vtt' }],
}, 0);
assert.equal(summary.host, 'cdn.example');
assert.equal(summary.stream_id.length, 16);
assert.deepEqual(summary.header_names, ['Authorization', 'Referer']);
assert.equal(JSON.stringify(summary).includes('token=secret'), false);
assert.equal(JSON.stringify(summary).includes('Authorization":"secret'), false);

assert.equal(classify({ ok: false, stream_count: 0 }, []), 'runtime_error');
assert.equal(classify({ ok: false, timed_out: true, stream_count: 0 }, []), 'runtime_timeout');
assert.equal(classify({ ok: true, stream_count: 0 }, []), 'runtime_empty');
assert.equal(classify({ ok: true, stream_count: 1 }, [{ playable: true }]), 'playable');
assert.equal(classify({ ok: true, stream_count: 1 }, [{ playable: true, identity: { status: 'contradiction' } }]), 'wrong_content');
assert.equal(classify({ ok: true, stream_count: 1 }, [{ playable: false, inconclusive: true }]), 'playback_inconclusive');
assert.equal(classify({ ok: true, stream_count: 1 }, [{ playable: false, inconclusive: false }]), 'media_unplayable');

const policyProviders = [
  { id: 'vf-good', manifest_enabled: true, is_vf: true, clients: { tv: { verdict: 'playable' }, desktop: { verdict: 'playable' } } },
  { id: 'non-vf-good', manifest_enabled: true, is_vf: false, clients: { tv: { verdict: 'playable' }, desktop: { verdict: 'playable' } } },
  { id: 'partial', manifest_enabled: true, is_vf: true, clients: { tv: { verdict: 'playable' }, desktop: { verdict: 'runtime_empty' } } },
  { id: 'disabled', manifest_enabled: false, is_vf: true, clients: { tv: { verdict: 'playable' }, desktop: { verdict: 'playable' } } },
];
const policy = summarizePolicy(policyProviders, ['tv', 'desktop'], { policy: { target_total: 3, minimum_vf: 1 } });
assert.equal(policy.verified_total, 2);
assert.equal(policy.verified_vf, 1);
assert.equal(policy.status, 'vf_met_total_shortfall');
assert.equal(policy.blocking_pass, true);
assert.deepEqual(policy.qualified_provider_ids, ['vf-good', 'non-vf-good']);
const strictIdentityPolicy = summarizePolicy([
  { id: 'verified', manifest_enabled: true, is_vf: true, clients: { tv: { verdict: 'playable', identity_status: 'verified' } } },
  { id: 'unknown', manifest_enabled: true, is_vf: true, clients: { tv: { verdict: 'playable', identity_status: 'unknown' } } },
], ['tv'], { policy: { target_total: 1, minimum_vf: 1, require_identity_match: true } });
assert.deepEqual(strictIdentityPolicy.qualified_provider_ids, ['verified']);
assert.equal(strictIdentityPolicy.status, 'target_met');
const recentWorkPolicy = summarizePolicy([], ['tv'], { policy: { target_total: 10, minimum_vf: 3 } });
assert.equal(recentWorkPolicy.objective_met, false);
assert.equal(recentWorkPolicy.advisory_only, true);
assert.equal(recentWorkPolicy.blocking_pass, true);

assert.deepEqual(streamIdentity({ title: 'Interstellar - 2014 - 1080p' }, { title: 'Interstellar', mediaType: 'movie' }), { status: 'match', reason: 'expected_title_alias' });
assert.deepEqual(streamIdentity({ title: 'Enola Holmes 2 - 1080p' }, { title: 'Mon ninja et moi 3', aliases: ['Checkered Ninja 3'], mediaType: 'movie' }), { status: 'contradiction', reason: 'strong_title_mismatch' });
assert.deepEqual(streamIdentity({ title: 'S02E04 1080p' }, { title: 'Revenant', mediaType: 'tv', season: 1, episode: 1 }), { status: 'contradiction', reason: 'wrong_season_episode' });
assert.deepEqual(streamIdentity({ title: 'Player - Ep 1 - VF [1080p]', name: 'Anime-Sama (VF)' }, { title: 'Jujutsu Kaisen', mediaType: 'tv', season: 1, episode: 1 }), { status: 'match', reason: 'episode_match' });
assert.deepEqual(streamIdentity({ title: 'S1E1 - Ryomen Sukuna', name: 'ToFlix' }, { title: 'Jujutsu Kaisen', mediaType: 'tv', season: 1, episode: 1 }), { status: 'match', reason: 'season_episode_match' });
assert.deepEqual(streamIdentity({ title: 'Saison 1 - Vidmoly', name: 'Mugiwara (VOSTFR)' }, { title: 'Mushoku Tensei', mediaType: 'tv', season: 1, episode: 1 }), { status: 'unknown', reason: 'insufficient_identity_metadata' });
assert.deepEqual(streamIdentity({ title: 'Enola Holmes 2 - 1080p' }, { title: 'Mon ninja et moi 3', forbiddenAliases: ['Enola Holmes 2'], mediaType: 'movie' }), { status: 'contradiction', reason: 'forbidden_title_alias' });

(async () => {
  let running = 0;
  let maximum = 0;
  const mapped = await mapLimit([1, 2, 3, 4], 2, async (value) => {
    running += 1;
    maximum = Math.max(maximum, running);
    await new Promise((resolve) => setTimeout(resolve, 5));
    running -= 1;
    return value * 2;
  });
  assert.deepEqual(mapped, [2, 4, 6, 8]);
  assert.equal(maximum, 2);
})().catch((error) => {
  process.stderr.write(`${error.stack || error}\n`);
  process.exitCode = 1;
});

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'nuvio-lab-test-'));
try {
  const runtimePath = path.join(tmp, 'tv', 'app/src/full/java/com/nuvio/tv/core/plugin/PluginRuntime.kt');
  fs.mkdirSync(path.dirname(runtimePath), { recursive: true });
  fs.writeFileSync(runtimePath, `
    private const val PLUGIN_TIMEOUT_MS = 60_000L
    val ua = "${WINDOWS_UA}"
    function("__native_fetch") { }
    var result = await getStreams(args.tmdbId, args.mediaType, args.season, args.episode)
  `);
  const contract = verifyRuntimeContract('tv', tmp);
  assert.equal(contract.ok, true, JSON.stringify(contract));
} finally {
  fs.rmSync(tmp, { recursive: true, force: true });
}

console.log('nuvio client lab tests passed');
