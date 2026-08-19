import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const script = path.join(root, 'engine_v2/scripts/diagnose-native-reader.mjs');
const b64 = (value) => Buffer.from(String(value)).toString('base64url');
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'niakvio-reader-brain-'));
try {
  const log = path.join(tmp, 'tv-native-corpus-sinners-2025.log');
  const output = path.join(tmp, 'brain.json');
  const common = [
    'FIELD_NATIVE_EVIDENCE_INSTRUMENTED client=tv',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=ui-launched screenshot=a.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=repository-load screenshot=repo-a.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=repository-http-request screenshot=repo-http-a.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=repository-http-response screenshot=repo-http-b.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=repository-loaded screenshot=repo-b.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=provider-load-state screenshot=repo-c.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=corpus-begin screenshot=b.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=provider-loading screenshot=c.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=provider-result screenshot=d.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=player-start screenshot=e.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=player-result screenshot=f.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=corpus-end screenshot=g.png bytes=100',
    'FIELD_NATIVE_REPOSITORY_LOAD_BEGIN client=tv fixture=sinners-2025 expected=2 manifest_host=raw.githubusercontent.com',
    'FIELD_NATIVE_REPOSITORY_HTTP_REQUEST client=tv kind=manifest method=GET endpoint=https://raw.githubusercontent.com/niakw/NiakVIO/sha/manifest.json request_header_names=accept',
    'FIELD_NATIVE_REPOSITORY_HTTP_RESPONSE client=tv kind=manifest method=GET endpoint=https://raw.githubusercontent.com/niakw/NiakVIO/sha/manifest.json status=200 duration_ms=20 response_header_names=content-type source=network',
    'FIELD_NATIVE_REPOSITORY_LOAD_RESULT client=tv fixture=sinners-2025 expected=2 loaded=2',
    `FIELD_NATIVE_PROVIDER_LOAD_RESULT client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} manifest_enabled=true runtime_enabled=true metadata_match=true`,
    `FIELD_NATIVE_PROVIDER_LOAD_RESULT client=tv fixture=sinners-2025 provider64=${b64('PURSTREAM')} manifest_enabled=true runtime_enabled=true metadata_match=true`,
    'FIELD_NATIVE_CORPUS_BEGIN client=tv fixture=sinners-2025 providers=2',
    `FIELD_NATIVE_PROVIDER_BEGIN client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} request_type=movie`,
    `FIELD_NATIVE_RESULT client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} request_type=movie enabled=true duration_ms=1 count=2`,
    `FIELD_NATIVE_PLAYER_BEGIN client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} request_type=movie index=0`,
    `FIELD_NATIVE_PLAYER client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} request_type=movie index=0 state=error engine=media3 http_status=403 failure_stage=http_access duration_seconds=0 host64=${b64('zip.example')} error_class64=${b64('PlaybackException')} error_code64=${b64('ERROR_CODE_IO_BAD_HTTP_STATUS')} exception_chain64=${b64('InvalidResponseCodeException')} response_header_names64=${b64('content-type,date')}`,
    `FIELD_NATIVE_PLAYER_BEGIN client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} request_type=movie index=1`,
    `FIELD_NATIVE_PLAYER client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} request_type=movie index=1 state=short_media engine=media3 http_status=0 failure_stage=duration_identity duration_seconds=20 host64=${b64('media.example')} error_class64=${b64('')} error_code64=${b64('')} exception_chain64=${b64('')} response_header_names64=${b64('')}`,
    `FIELD_NATIVE_PROVIDER_BEGIN client=tv fixture=sinners-2025 provider64=${b64('PURSTREAM')} request_type=movie`,
    `FIELD_NATIVE_RESULT client=tv fixture=sinners-2025 provider64=${b64('PURSTREAM')} request_type=movie enabled=true duration_ms=1 count=1`,
    `FIELD_NATIVE_PLAYER_BEGIN client=tv fixture=sinners-2025 provider64=${b64('PURSTREAM')} request_type=movie index=0`,
    `FIELD_NATIVE_PLAYER client=tv fixture=sinners-2025 provider64=${b64('PURSTREAM')} request_type=movie index=0 state=ready engine=media3 http_status=0 failure_stage=none duration_seconds=8220 host64=${b64('media.example')} error_class64=${b64('')} error_code64=${b64('')} exception_chain64=${b64('')} response_header_names64=${b64('')}`,
    'FIELD_NATIVE_CORPUS_END client=tv fixture=sinners-2025 errors=0',
  ];
  fs.writeFileSync(log, common.join('\n') + '\n');
  const run = spawnSync(process.execPath, [script, '--output', output, log], { cwd: root, encoding: 'utf8' });
  assert.equal(run.status, 0, run.stderr + run.stdout);
  const data = JSON.parse(fs.readFileSync(output, 'utf8'));
  assert.equal(data.brainVersion, 4);
  assert.equal(data.schemaVersion, 5);
  assert.equal(data.evidenceComplete, true);
  assert.equal(data.policy.learningAllowed, true);
  assert.equal(data.policy.providerLoadJsMutationAllowed, false);
  assert.equal(data.readerObserved, 3);
  assert.equal(data.readerHealthy, 1);
  assert.equal(data.readerFailures, 2);
  assert.equal(data.evidenceStats.providerLoads, 2);
  assert.equal(data.evidenceStats.repositoryHttpRequests, 1);
  assert.equal(data.providerLoadIssues.length, 0);
  const access = data.plans.find((row) => row.failureClass === 'playback_http_access');
  assert.ok(access);
  assert.equal(access.requestType, 'movie');
  assert.match(access.signature, /^movie:/);
  assert.equal(access.httpStatus, 403);
  assert.equal(access.hypotheses[0].id, 'replay-native-request-context');
  const short = data.plans.find((row) => row.failureClass === 'short_media');
  assert.ok(short);
  assert.equal(short.durationSeconds, 20);
  assert.equal(short.hypotheses[0].id, 'reject-short-or-preview-media');
  assert.equal(data.policy.requireFreshNativeReaderProofAfterRepair, true);
  assert.match(data.privacy, /No raw URLs/);
  assert.match(run.stdout, /FIELD_NATIVE_READER_BRAIN evidence_complete=true/);

  // A provider can fail after repository installation but before any execution/
  // reader route. Complete loading/network/traversal evidence makes this actionable
  // repository/Core evidence, not an incomplete lab.
  const loadFailure = path.join(tmp, 'provider-load-failure.log');
  const loadFailureOutput = path.join(tmp, 'provider-load-failure.json');
  fs.writeFileSync(loadFailure, [
    'FIELD_NATIVE_EVIDENCE_INSTRUMENTED client=tv',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=ui-launched screenshot=a.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=repository-load screenshot=b.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=repository-http-request screenshot=bh.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=repository-http-response screenshot=bi.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=repository-loaded screenshot=c.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=provider-load-state screenshot=d.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=corpus-begin screenshot=e.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=corpus-end screenshot=f.png bytes=100',
    'FIELD_NATIVE_REPOSITORY_LOAD_BEGIN client=tv fixture=sinners-2025 expected=1 manifest_host=raw.githubusercontent.com',
    'FIELD_NATIVE_REPOSITORY_HTTP_REQUEST client=tv kind=manifest method=GET endpoint=https://raw.githubusercontent.com/niakw/NiakVIO/sha/manifest.json request_header_names=accept',
    'FIELD_NATIVE_REPOSITORY_HTTP_RESPONSE client=tv kind=manifest method=GET endpoint=https://raw.githubusercontent.com/niakw/NiakVIO/sha/manifest.json status=200 duration_ms=20 response_header_names=content-type source=network',
    'FIELD_NATIVE_REPOSITORY_LOAD_RESULT client=tv fixture=sinners-2025 expected=1 loaded=0',
    `FIELD_NATIVE_PROVIDER_LOAD_ERROR client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} reason=missing_after_repository_install`,
    'FIELD_NATIVE_CORPUS_BEGIN client=tv fixture=sinners-2025 providers=1',
    `FIELD_NATIVE_PROVIDER_SKIPPED client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} enabled=false requested_type=movie reason=load_failure`,
    'FIELD_NATIVE_CORPUS_END client=tv fixture=sinners-2025 errors=0',
  ].join('\n') + '\n');
  const loadFailureRun = spawnSync(process.execPath, [script, '--output', loadFailureOutput, loadFailure], { cwd: root, encoding: 'utf8' });
  assert.equal(loadFailureRun.status, 0, loadFailureRun.stderr + loadFailureRun.stdout);
  const loadFailureData = JSON.parse(fs.readFileSync(loadFailureOutput, 'utf8'));
  assert.equal(loadFailureData.evidenceComplete, true);
  assert.equal(loadFailureData.readerObserved, 0);
  assert.equal(loadFailureData.providerLoadActionableFailures, 1);
  assert.deepEqual(loadFailureData.plans, []);
  assert.equal(loadFailureData.providerLoadIssues[0].failureClass, 'provider_repository_load_missing');
  assert.equal(loadFailureData.providerLoadIssues[0].providerJsMutationAllowed, false);
  assert.equal(loadFailureData.providerLoadIssues[0].coreOrManifestProposalAllowed, true);
  assert.equal(loadFailureData.providerLoadPriorities[0].layer, 'repository');
  assert.equal(loadFailureData.providerOutcomes[0].loadFailures, 1);
  assert.equal(loadFailureData.policy.repositoryLearningAllowed, true);
  assert.equal(loadFailureData.policy.providerLoadJsMutationAllowed, false);
  assert.match(loadFailureRun.stdout, /provider_load_failures=1/);

  // A whole repository can fail before any provider or player runs. The HTTP 404,
  // terminal repository error and per-provider fallout are still a complete proof.
  // The Brain may propose Core/repository work but must never generate provider JS.
  const installFailure = path.join(tmp, 'repository-install-failure.log');
  const installFailureOutput = path.join(tmp, 'repository-install-failure.json');
  fs.writeFileSync(installFailure, [
    'FIELD_NATIVE_EVIDENCE_INSTRUMENTED client=tv',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=ui-launched screenshot=a.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=repository-load screenshot=b.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=repository-http-request screenshot=c.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=repository-http-response screenshot=d.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=repository-load-error screenshot=e.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=provider-load-state screenshot=f.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=corpus-begin screenshot=g.png bytes=100',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase=corpus-end screenshot=h.png bytes=100',
    'FIELD_NATIVE_REPOSITORY_LOAD_BEGIN client=tv fixture=sinners-2025 expected=1 manifest_host=raw.githubusercontent.com',
    'FIELD_NATIVE_REPOSITORY_HTTP_REQUEST client=tv kind=manifest method=GET endpoint=https://raw.githubusercontent.com/niakw/NiakVIO/sha/manifest.json request_header_names=accept',
    'FIELD_NATIVE_REPOSITORY_HTTP_RESPONSE client=tv kind=manifest method=GET endpoint=https://raw.githubusercontent.com/niakw/NiakVIO/sha/manifest.json status=404 duration_ms=12 response_header_names=content-type source=network',
    `FIELD_NATIVE_REPOSITORY_LOAD_ERROR client=tv fixture=sinners-2025 reason=install_failed error64=${b64('HTTP 404')}`,
    `FIELD_NATIVE_PROVIDER_LOAD_ERROR client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} reason=repository_install_failed`,
    'FIELD_NATIVE_CORPUS_BEGIN client=tv fixture=sinners-2025 providers=1',
    `FIELD_NATIVE_PROVIDER_SKIPPED client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} enabled=false requested_type=movie reason=load_failure`,
    'FIELD_NATIVE_CORPUS_END client=tv fixture=sinners-2025 errors=0',
  ].join('\n') + '\n');
  const installFailureRun = spawnSync(process.execPath, [script, '--output', installFailureOutput, installFailure], { cwd: root, encoding: 'utf8' });
  assert.equal(installFailureRun.status, 0, installFailureRun.stderr + installFailureRun.stdout);
  const installFailureData = JSON.parse(fs.readFileSync(installFailureOutput, 'utf8'));
  assert.equal(installFailureData.evidenceComplete, true);
  assert.equal(installFailureData.evidenceStats.repositoryLoadFailures, 1);
  assert.equal(installFailureData.evidenceStats.repositoryHttpRequests, 1);
  assert.equal(installFailureData.readerObserved, 0);
  assert.equal(installFailureData.providerLoadActionableFailures, 1);
  assert.equal(installFailureData.providerLoadIssues[0].failureClass, 'provider_repository_load_error');
  assert.equal(installFailureData.providerLoadIssues[0].providerJsMutationAllowed, false);
  assert.equal(installFailureData.providerLoadIssues[0].coreOrManifestProposalAllowed, true);
  assert.deepEqual(installFailureData.plans, []);

  // Metadata drift at load time belongs to manifest/Core semantics, never JS repair.
  const metadataFailure = path.join(tmp, 'provider-metadata-failure.log');
  const metadataFailureOutput = path.join(tmp, 'provider-metadata-failure.json');
  fs.writeFileSync(metadataFailure, fs.readFileSync(loadFailure, 'utf8')
    .replace('missing_after_repository_install', 'metadata_or_code_mismatch'));
  const metadataRun = spawnSync(process.execPath, [script, '--output', metadataFailureOutput, metadataFailure], { cwd: root, encoding: 'utf8' });
  assert.equal(metadataRun.status, 0, metadataRun.stderr + metadataRun.stdout);
  const metadataData = JSON.parse(fs.readFileSync(metadataFailureOutput, 'utf8'));
  assert.equal(metadataData.providerLoadIssues[0].failureClass, 'provider_repository_metadata_mismatch');
  assert.equal(metadataData.providerLoadIssues[0].layer, 'manifest_contract');
  assert.deepEqual(metadataData.plans, []);

  // A log can look structurally complete yet still be causally unusable if the
  // Nuvio media route was not recorded. The Brain must refuse to learn from it.
  const routeMissing = path.join(tmp, 'route-missing.log');
  const routeMissingOutput = path.join(tmp, 'route-missing.json');
  fs.writeFileSync(routeMissing, common.map((line) => line.replace(/ request_type=movie/g, '')).join('\n') + '\n');
  const routeRefused = spawnSync(process.execPath, [script, '--output', routeMissingOutput, routeMissing], { cwd: root, encoding: 'utf8' });
  assert.equal(routeRefused.status, 2, routeRefused.stderr + routeRefused.stdout);
  const routeRefusedData = JSON.parse(fs.readFileSync(routeMissingOutput, 'utf8'));
  assert.equal(routeRefusedData.evidenceComplete, false);
  assert.equal(routeRefusedData.policy.learningAllowed, false);
  assert.equal(routeRefusedData.policy.repairPlanningAllowed, false);
  assert.deepEqual(routeRefusedData.plans, []);
  assert.ok(routeRefusedData.evidenceProblems.some((problem) => problem.startsWith('invalid_request_type:')));

  // Likewise, direct PluginRuntime evidence without proof that Nuvio actually
  // installed/reconstructed the providers is no longer sufficient.
  const loadMissing = path.join(tmp, 'load-missing.log');
  const loadMissingOutput = path.join(tmp, 'load-missing.json');
  const withoutLoading = common.filter((line) =>
    !line.includes('repository-load') &&
    !line.includes('repository-loaded') &&
    !line.includes('repository-http') &&
    !line.includes('provider-load-state') &&
    !line.startsWith('FIELD_NATIVE_REPOSITORY_LOAD_') &&
    !line.startsWith('FIELD_NATIVE_REPOSITORY_HTTP_') &&
    !line.startsWith('FIELD_NATIVE_PROVIDER_LOAD_')
  );
  fs.writeFileSync(loadMissing, withoutLoading.join('\n') + '\n');
  const loadRefused = spawnSync(process.execPath, [script, '--output', loadMissingOutput, loadMissing], { cwd: root, encoding: 'utf8' });
  assert.equal(loadRefused.status, 2, loadRefused.stderr + loadRefused.stdout);
  const loadRefusedData = JSON.parse(fs.readFileSync(loadMissingOutput, 'utf8'));
  assert.equal(loadRefusedData.evidenceComplete, false);
  assert.equal(loadRefusedData.policy.learningAllowed, false);
  assert.deepEqual(loadRefusedData.plans, []);
  assert.ok(loadRefusedData.evidenceProblems.some((problem) => problem.startsWith('missing_repository_load:')));

  const incomplete = path.join(tmp, 'incomplete.log');
  const incompleteOutput = path.join(tmp, 'incomplete.json');
  fs.writeFileSync(incomplete, [
    'FIELD_NATIVE_CORPUS_BEGIN client=tv fixture=sinners-2025 providers=1',
    `FIELD_NATIVE_PLAYER client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} request_type=movie index=0 state=error engine=media3 http_status=403 failure_stage=http_access`,
  ].join('\n') + '\n');
  const refused = spawnSync(process.execPath, [script, '--output', incompleteOutput, incomplete], { cwd: root, encoding: 'utf8' });
  assert.equal(refused.status, 2, refused.stderr + refused.stdout);
  const refusedData = JSON.parse(fs.readFileSync(incompleteOutput, 'utf8'));
  assert.equal(refusedData.evidenceComplete, false);
  assert.equal(refusedData.policy.learningAllowed, false);
  assert.equal(refusedData.policy.repairPlanningAllowed, false);
  assert.deepEqual(refusedData.plans, []);
  assert.ok(refusedData.evidenceProblems.length > 0);
  assert.match(refused.stdout, /FIELD_NATIVE_READER_BRAIN_EVIDENCE_INCOMPLETE/);
} finally {
  fs.rmSync(tmp, { recursive: true, force: true });
}
console.log('targeted native reader Brain diagnosis tests passed');
