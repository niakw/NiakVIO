'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { assessNativeEvidence } = require('../scripts/native_evidence_completeness.cjs');

function writeLog(dir, name, lines) {
  const file = path.join(dir, name);
  fs.writeFileSync(file, `${lines.join('\n')}\n`);
  return file;
}

function baseEvidence(routeLines, frontendLines) {
  return [
    'FIELD_NATIVE_CORPUS_BEGIN client=tv fixture=sinners-2025 providers=1',
    'FIELD_NATIVE_EVIDENCE_INSTRUMENTED client=tv',
    'FIELD_NATIVE_REPOSITORY_LOAD_BEGIN client=tv fixture=sinners-2025 expected=1',
    'FIELD_NATIVE_REPOSITORY_CACHE_HIT client=tv fixture=sinners-2025',
    'FIELD_NATIVE_REPOSITORY_LOAD_RESULT client=tv fixture=sinners-2025',
    'FIELD_NATIVE_PROVIDER_LOAD_RESULT client=tv fixture=sinners-2025 provider=test',
    ...routeLines,
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=ui-launched',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=corpus-begin',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=repository-load',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=repository-loaded',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=provider-load-state',
    ...frontendLines,
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=corpus-end',
    'FIELD_NATIVE_CORPUS_END client=tv fixture=sinners-2025',
  ];
}

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'niakvio-native-evidence-'));
try {
  const skippedOnly = writeLog(tmp, 'skipped-only.log', baseEvidence([
    'FIELD_NATIVE_PROVIDER_SKIPPED client=tv fixture=sinners-2025 provider=test reason=unsupported_type',
  ], []));
  const skippedAssessment = assessNativeEvidence([skippedOnly]);
  assert.equal(skippedAssessment.complete, false, 'skipped-only corpus must never be complete');
  assert.ok(
    skippedAssessment.problems.includes('missing_provider_execution:tv:sinners-2025'),
    `missing execution problem not reported: ${JSON.stringify(skippedAssessment.problems)}`,
  );
  assert.equal(skippedAssessment.stats.providerExecutions, 0);

  const executedNoPlayer = writeLog(tmp, 'executed-no-player.log', baseEvidence([
    'FIELD_NATIVE_PROVIDER_BEGIN client=tv fixture=sinners-2025 provider=test request_type=movie',
    'FIELD_NATIVE_RESULT client=tv fixture=sinners-2025 provider=test request_type=movie returned=0',
  ], [
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=provider-loading',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=provider-result',
  ]));
  const executedAssessment = assessNativeEvidence([executedNoPlayer]);
  assert.equal(
    executedAssessment.complete,
    true,
    `real provider execution with zero returned streams remains valid evidence: ${JSON.stringify(executedAssessment.problems)}`,
  );
  assert.equal(executedAssessment.stats.providerExecutions, 1);
  assert.equal(executedAssessment.stats.playerProbes, 0);

  console.log('native evidence completeness execution-floor tests passed');
} finally {
  fs.rmSync(tmp, { recursive: true, force: true });
}
