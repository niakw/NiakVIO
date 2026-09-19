#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { assessNativeEvidence } = require('../../scripts/native_evidence_completeness.cjs');
const { analyzeMediaTypeCapabilities } = require('../../scripts/analyze_native_media_type_capabilities.cjs');

const args = process.argv.slice(2);
const outputIndex = args.indexOf('--output');
const outputPath = outputIndex >= 0 && args[outputIndex + 1]
  ? path.resolve(args[outputIndex + 1])
  : path.resolve('native-media-capabilities-brain.json');
const logPaths = args
  .filter((value, index) => index !== outputIndex && index !== outputIndex + 1 && value !== '--output')
  .map((value) => path.resolve(value));

if (!logPaths.length) {
  console.error('usage: node engine_v2/scripts/diagnose-native-media-capabilities.mjs [--output file.json] <log> [log ...]');
  process.exit(64);
}

function fields(line) {
  const out = {};
  const re = /([A-Za-z0-9_]+)=([^\s]+)/g;
  let match;
  while ((match = re.exec(line)) !== null) out[match[1]] = match[2];
  return out;
}

const evidence = assessNativeEvidence(logPaths);
const fixtures = new Set();
for (const file of logPaths) {
  if (!fs.existsSync(file)) continue;
  for (const raw of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    const marker = raw.indexOf('FIELD_NATIVE_');
    if (marker < 0) continue;
    const f = fields(raw.slice(marker));
    if (f.fixture) fixtures.add(f.fixture);
  }
}

const reports = evidence.complete
  ? [...fixtures].sort().map((fixture) => analyzeMediaTypeCapabilities(fixture, logPaths))
  : [];
const proposals = reports.flatMap((report) => report.proposals || []);

const payload = {
  schemaVersion: 1,
  generatedAt: new Date().toISOString(),
  evidenceComplete: evidence.complete,
  evidenceProblems: evidence.problems,
  evidenceStats: evidence.stats,
  fixtureReports: reports,
  proposals,
  policy: {
    learningAllowed: evidence.complete,
    productionManifestMutationAllowed: false,
    requireIdentityProof: true,
    requireEveryReturnedStreamHealthy: true,
    requireCrossDeviceConfirmation: true,
  },
};

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, JSON.stringify(payload, null, 2) + '\n');
console.log(`FIELD_NATIVE_MEDIA_CAPABILITY_BRAIN evidence_complete=${payload.evidenceComplete} fixtures=${reports.length} proposals=${proposals.length}`);
for (const proposal of proposals.slice(0, 80)) {
  console.log(`FIELD_NATIVE_MEDIA_CAPABILITY_BRAIN_PROPOSAL ${JSON.stringify(proposal)}`);
}
if (!evidence.complete) process.exitCode = 2;
