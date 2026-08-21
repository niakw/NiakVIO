#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


# Brain: provider executions returning zero streams are meaningful provider/media
# extraction evidence even though no player can be launched.
path = "engine_v2/scripts/diagnose-native-reader.mjs"
text = read(path)
text = replace_once(
    text,
    "const readerRows = [];\nconst providerLoadObservations = [];\n",
    "const readerRows = [];\nconst providerResultRows = [];\nconst providerLoadObservations = [];\n",
    path,
)
text = replace_once(
    text,
    "    const marker = raw.indexOf('FIELD_NATIVE_PLAYER ');\n    if (marker < 0) continue;\n",
    """    const resultAt = raw.indexOf('FIELD_NATIVE_RESULT ');
    if (resultAt >= 0) {
      const f = fields(raw.slice(resultAt).trim());
      providerResultRows.push({
        client: f.client || 'unknown',
        fixture: f.fixture || 'unknown',
        provider: decode(f.provider64 || '').toLowerCase() || String(f.provider || '').toLowerCase(),
        requestType: String(f.request_type || 'unknown').toLowerCase(),
        routeMode: String(f.route_mode || 'declared').toLowerCase(),
        enabled: String(f.enabled || 'true').toLowerCase() !== 'false',
        count: Math.max(0, Number(f.count ?? f.returned ?? 0) || 0),
      });
    }

    const marker = raw.indexOf('FIELD_NATIVE_PLAYER ');
    if (marker < 0) continue;
""",
    path,
)
text = replace_once(text, "const plans = evidence.complete ? providerEligibleFailures.map((row) => {\n", "const readerPlans = evidence.complete ? providerEligibleFailures.map((row) => {\n", path)
text = replace_once(
    text,
    "}) : [];\n\nconst providerLoadIssues = evidence.complete ? providerLoadObservations.map((row) => ({\n",
    """}) : [];

const zeroResultRows = providerResultRows.filter((row) =>
  row.enabled && row.routeMode !== 'capability_probe' && row.count === 0
);
const zeroResultPlans = evidence.complete ? zeroResultRows.map((row) => {
  const signature = `${row.requestType}:media_extraction_gap:${row.provider}:${row.fixture}`;
  const plan = planRepair({
    invoked: true,
    signature,
    request: { mediaType: row.requestType },
    stages: {
      provider: { attempted: true, matched: true, returned: 0 },
      media: { attempted: true, found: false },
    },
  }, { signature, maxHypotheses: 3 });
  return {
    provider: row.provider, client: row.client, fixture: row.fixture,
    requestType: row.requestType, routeMode: row.routeMode, index: -1,
    state: 'zero_streams', failureClass: plan.failureClass, failureDomain: 'provider',
    providerMutationEligible: true, failureStage: 'media_extraction',
    httpStatus: 0, errorCode: '', errorClass: '', host: '', durationSeconds: null,
    loadBytes: 0, loadDurationMs: 0, mediaDataType: -1, trackType: -1,
    signature, action: plan.action, exitReason: plan.exitReason,
    hypotheses: plan.hypotheses.map((hypothesis) => ({
      id: hypothesis.id,
      capabilities: [...(hypothesis.capabilities || [])],
      actions: [...(hypothesis.actions || [])],
    })),
  };
}) : [];
const plans = [...readerPlans, ...zeroResultPlans];

const providerLoadIssues = evidence.complete ? providerLoadObservations.map((row) => ({
""",
    path,
)
text = replace_once(
    text,
    "const healthyByRoute = new Map();\nfor (const row of declaredHealthy) {\n",
    """const healthyByRoute = new Map();
for (const row of providerResultRows.filter((row) => row.enabled && row.routeMode !== 'capability_probe' && row.count > 0)) {
  const key = `${String(row.provider || '').toLowerCase()}\u0000${row.requestType}\u0000${row.fixture}`;
  if (!healthyByRoute.has(key)) healthyByRoute.set(key, new Set());
  healthyByRoute.get(key).add(row.client);
}
for (const row of declaredHealthy) {
""",
    path,
)
old = """const observations = readerRows.map((row) => ({
  provider: String(row.provider || '').toLowerCase(), client: row.client, fixture: row.fixture,
  requestType: row.requestType, routeMode: row.routeMode, index: row.index,
  state: row.state, failureClass: row.failureClass, failureDomain: row.failureDomain,
  providerMutationEligible: row.providerMutationEligible, failureStage: row.failureStage,
  httpStatus: row.httpStatus, errorCode: row.errorCode, host: row.host,
  durationSeconds: row.durationSeconds, loadBytes: row.loadBytes, loadDurationMs: row.loadDurationMs,
}));
"""
new = """const observations = [
  ...providerResultRows.map((row) => ({
    provider: row.provider, client: row.client, fixture: row.fixture,
    requestType: row.requestType, routeMode: row.routeMode, index: -1,
    state: row.count > 0 ? 'streams_returned' : 'zero_streams',
    failureClass: row.enabled && row.routeMode !== 'capability_probe' && row.count === 0 ? 'media_extraction_gap' : 'healthy',
    failureDomain: row.enabled && row.routeMode !== 'capability_probe' && row.count === 0 ? 'provider' : 'none',
    providerMutationEligible: row.enabled && row.routeMode !== 'capability_probe' && row.count === 0,
    failureStage: row.count === 0 ? 'media_extraction' : 'none',
    httpStatus: 0, errorCode: '', host: '', durationSeconds: null, loadBytes: 0, loadDurationMs: 0,
    enabled: row.enabled, count: row.count, observationType: 'provider_result',
  })),
  ...readerRows.map((row) => ({
    provider: String(row.provider || '').toLowerCase(), client: row.client, fixture: row.fixture,
    requestType: row.requestType, routeMode: row.routeMode, index: row.index,
    state: row.state, failureClass: row.failureClass, failureDomain: row.failureDomain,
    providerMutationEligible: row.providerMutationEligible, failureStage: row.failureStage,
    httpStatus: row.httpStatus, errorCode: row.errorCode, host: row.host,
    durationSeconds: row.durationSeconds, loadBytes: row.loadBytes, loadDurationMs: row.loadDurationMs,
    observationType: 'player',
  })),
];
"""
text = replace_once(text, old, new, path)
text = replace_once(text, "  schemaVersion: 5,\n", "  schemaVersion: 6,\n", path)
text = replace_once(text, "  readerObserved: readerRows.length,\n", "  providerResultObserved: providerResultRows.length,\n  providerZeroResults: zeroResultRows.length,\n  readerObserved: readerRows.length,\n", path)
write(path, text)

# Global, provider-agnostic media repair skill also applies to media extraction gaps.
path = "scripts/build_native_reader_brain_repair.py"
text = read(path)
text = replace_once(
    text,
    'HYPOTHESIS_SKILLS: dict[str, tuple[str, ...]] = {\n',
    'HYPOTHESIS_SKILLS: dict[str, tuple[str, ...]] = {\n    "capture-media-network": ("global_media_enrichment_v1",),\n    "inspect-player-javascript": ("global_media_enrichment_v1",),\n',
    path,
)
write(path, text)

# Core owns presentation. Source-less 1080p follows the requested Blu-ray product
# convention while an explicit WEB-DL/WEBRIP/etc always wins. Exact resolution stays visible.
path = "engine_v2/src/stream-presentation.mjs"
text = read(path)
text = replace_once(
    text,
    "    sourceType: normalizeSourceType(stream.sourceType ?? stream.source_type ?? stream.releaseType ?? stream.release_type),\n",
    "    sourceType: inferSourceType(\n      stream.sourceType ?? stream.source_type ?? stream.releaseType ?? stream.release_type,\n      stream.quality ?? stream.resolution,\n    ),\n",
    path,
)
text = replace_once(text, "  const sourceType = normalizeSourceType(facts.sourceType);\n", "  const sourceType = inferSourceType(facts.sourceType, facts.quality);\n", path)
text = replace_once(
    text,
    '  if (quality) out.push(quality === "2160p" ? "【4K】" : `【${quality.toUpperCase()}】`);\n  if (sourceType) out.push(`【${sourceType}】`);\n',
    '  if (quality === "2160p") out.push("【4K】", "2160p");\n  else if (quality === "1080p" && sourceType === "BLU-RAY") out.push("【BLU-RAY】", "1080p");\n  else if (quality) out.push(`【${quality.toUpperCase()}】`);\n  if (sourceType && !(quality === "1080p" && sourceType === "BLU-RAY")) out.push(`【${sourceType}】`);\n',
    path,
)
text = text.replace('  if (ageRating) out.push(`🔞 ${ageRating}`);', '  if (ageRating) out.push(`⚠ ${ageRating}`);')
text = replace_once(
    text,
    "export function normalizeSourceType(value) {\n",
    'export function inferSourceType(value, quality = null) {\n  const explicit = normalizeSourceType(value);\n  if (explicit) return explicit;\n  return normalizeQuality(quality) === "1080p" ? "BLU-RAY" : null;\n}\n\nexport function normalizeSourceType(value) {\n',
    path,
)
text = text.replace(
    "  // Unknown strings are not provenance. In particular, a quality such as 1080p\n  // must never be converted into a source badge or used to imply Blu-ray/Web-DL.\n  return null;",
    "  // Unknown strings are not explicit provenance. The separate inference layer may\n  // apply the product convention that source-less 1080p is displayed as Blu-ray.\n  return null;",
)
write(path, text)

path = "engine_v2/tests/stream-presentation.test.mjs"
text = read(path)
text = text.replace("  normalizeSourceType,\n", "  normalizeSourceType,\n  inferSourceType,\n")
text = text.replace("assert.match(presented.description, /🔞 -12/);", "assert.match(presented.description, /⚠ -12/);")
text = text.replace("assert.match(tmdbFallback.description, /🔞 16\\+/);", "assert.match(tmdbFallback.description, /⚠ 16\\+/);")
old = '''const noInventedBluray = presentStreamCandidate({
  name: "FrenchStream",
  url: "https://media.example/1080.mp4",
  quality: "1080p",
}, {}, { name: "FrenchStream" });
assert.match(noInventedBluray.description, /【1080P】/);
assert.doesNotMatch(noInventedBluray.description, /BLU-RAY/i);
assert.equal(normalizeSourceType("1080p"), null);
assert.equal(normalizeSourceType("some provider label"), null);
'''
new = '''const inferredBluray = presentStreamCandidate({
  name: "FrenchStream",
  url: "https://media.example/1080.mp4",
  quality: "1080p",
}, {}, { name: "FrenchStream" });
assert.match(inferredBluray.description, /【BLU-RAY】/);
assert.match(inferredBluray.description, /1080p/);
assert.equal(inferredBluray.sourceType, "BLU-RAY");
assert.equal(inferSourceType(null, "1080p"), "BLU-RAY");
assert.equal(normalizeSourceType("1080p"), null);
assert.equal(normalizeSourceType("some provider label"), null);

const explicitWebDl = presentStreamCandidate({
  name: "Cineby",
  url: "https://media.example/1080.mp4",
  quality: "1080p",
  sourceType: "WEB-DL",
}, {}, { name: "Cineby" });
assert.match(explicitWebDl.description, /【1080P】/);
assert.match(explicitWebDl.description, /【WEB-DL】/);
assert.doesNotMatch(explicitWebDl.description, /BLU-RAY/);
assert.equal(explicitWebDl.sourceType, "WEB-DL");

const preserved4k = presentStreamCandidate({
  name: "Movix",
  url: "https://media.example/2160.m3u8",
  quality: "2160p",
}, {}, { name: "Movix" });
assert.match(preserved4k.description, /【4K】/);
assert.match(preserved4k.description, /2160p/);
'''
text = replace_once(text, old, new, path)
text = text.replace('assert.deepEqual(badges, ["【4K】", "🌐 VFQ", "🎞 H.264"]);', 'assert.deepEqual(badges, ["【4K】", "2160p", "🌐 VFQ", "🎞 H.264"]);')
write(path, text)

# New focused regression test for count=0 diagnosis and consensus semantics.
write("engine_v2/tests/native-reader-zero-result.test.mjs", r'''import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const script = path.join(root, 'engine_v2/scripts/diagnose-native-reader.mjs');
const b64 = (value) => Buffer.from(String(value)).toString('base64url');

function logFor(client, rows) {
  const fixture = 'sinners-2025';
  const lines = [
    `FIELD_NATIVE_EVIDENCE_INSTRUMENTED client=${client}`,
    `FIELD_NATIVE_REPOSITORY_LOAD_BEGIN client=${client} fixture=${fixture} expected=${rows.length}`,
    `FIELD_NATIVE_REPOSITORY_CACHE_HIT client=${client} fixture=${fixture}`,
    `FIELD_NATIVE_REPOSITORY_LOAD_RESULT client=${client} fixture=${fixture}`,
    `FIELD_NATIVE_CORPUS_BEGIN client=${client} fixture=${fixture} providers=${rows.length}`,
    `FIELD_NATIVE_FRONTEND_CAPTURE client=${client} fixture=${fixture} phase=ui-launched`,
    `FIELD_NATIVE_FRONTEND_CAPTURE client=${client} fixture=${fixture} phase=corpus-begin`,
    `FIELD_NATIVE_FRONTEND_CAPTURE client=${client} fixture=${fixture} phase=repository-load`,
    `FIELD_NATIVE_FRONTEND_CAPTURE client=${client} fixture=${fixture} phase=repository-loaded`,
    `FIELD_NATIVE_FRONTEND_CAPTURE client=${client} fixture=${fixture} phase=provider-load-state`,
    `FIELD_NATIVE_FRONTEND_CAPTURE client=${client} fixture=${fixture} phase=provider-loading`,
    `FIELD_NATIVE_FRONTEND_CAPTURE client=${client} fixture=${fixture} phase=provider-result`,
  ];
  for (const row of rows) {
    lines.push(`FIELD_NATIVE_PROVIDER_LOAD_RESULT client=${client} fixture=${fixture} provider64=${b64(row.provider)} manifest_enabled=${row.enabled} runtime_enabled=${row.enabled} metadata_match=true`);
    lines.push(`FIELD_NATIVE_PROVIDER_BEGIN client=${client} fixture=${fixture} provider64=${b64(row.provider)} request_type=${row.requestType} route_mode=${row.routeMode}`);
    lines.push(`FIELD_NATIVE_RESULT client=${client} fixture=${fixture} provider64=${b64(row.provider)} request_type=${row.requestType} route_mode=${row.routeMode} enabled=${row.enabled} count=${row.count}`);
  }
  lines.push(`FIELD_NATIVE_FRONTEND_CAPTURE client=${client} fixture=${fixture} phase=corpus-end`);
  lines.push(`FIELD_NATIVE_CORPUS_END client=${client} fixture=${fixture} errors=0`);
  return lines.join('\n') + '\n';
}

function diagnose(files, output) {
  const run = spawnSync(process.execPath, [script, '--output', output, ...files], { cwd: root, encoding: 'utf8' });
  assert.equal(run.status, 0, run.stderr + run.stdout);
  return JSON.parse(fs.readFileSync(output, 'utf8'));
}

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'niakvio-zero-result-'));
try {
  const rows = [
    { provider: 'ZERO', enabled: true, count: 0, requestType: 'movie', routeMode: 'declared' },
    { provider: 'DISABLED', enabled: false, count: 0, requestType: 'movie', routeMode: 'declared' },
    { provider: 'CAPABILITY', enabled: true, count: 0, requestType: 'tv', routeMode: 'capability_probe' },
    { provider: 'POSITIVE', enabled: true, count: 2, requestType: 'movie', routeMode: 'declared' },
  ];
  const tv = path.join(tmp, 'tv.log');
  fs.writeFileSync(tv, logFor('tv', rows));
  const one = diagnose([tv], path.join(tmp, 'one.json'));
  assert.equal(one.schemaVersion, 6);
  assert.equal(one.evidenceComplete, true);
  assert.equal(one.providerResultObserved, 4);
  assert.equal(one.providerZeroResults, 1);
  assert.equal(one.plans.length, 1);
  assert.equal(one.plans[0].provider, 'zero');
  assert.equal(one.plans[0].failureClass, 'media_extraction_gap');
  assert.equal(one.plans[0].hypotheses[0].id, 'capture-media-network');
  assert.equal(one.policy.providerLearningAllowed, false);
  assert.equal(one.crossClientProviderFailureGroups, 0);
  assert.ok(!one.plans.some((plan) => plan.provider === 'disabled'));
  assert.ok(!one.plans.some((plan) => plan.provider === 'capability'));
  const positive = one.observations.find((row) => row.provider === 'positive' && row.observationType === 'provider_result');
  assert.equal(positive.failureClass, 'healthy');

  const desktop = path.join(tmp, 'desktop.log');
  fs.writeFileSync(desktop, logFor('desktop', rows));
  const two = diagnose([tv, desktop], path.join(tmp, 'two.json'));
  assert.equal(two.evidenceComplete, true);
  assert.equal(two.crossClientProviderFailureGroups, 1);
  assert.equal(two.policy.providerLearningAllowed, true);
  assert.equal(two.plans.filter((plan) => plan.provider === 'zero').length, 2);

  console.log('native reader zero-result diagnosis consensus tests passed');
} finally {
  fs.rmSync(tmp, { recursive: true, force: true });
}
''')

print("FIELD_SCRATCH_PATCH brain_core_fixes=applied")
