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
    `FIELD_NATIVE_PLAYER client=tv fixture=sinners-2025 provider64=${b64('PURSTREAM')} request_type=movie index=0 state=ready engine=media3 http_status=0 failure_stage=none video_width=1280 video_height=720 audio_track_count=1 duration_seconds=8220 host64=${b64('media.example')} error_class64=${b64('')} error_code64=${b64('')} exception_chain64=${b64('')} response_header_names64=${b64('')}`,
    'FIELD_NATIVE_CORPUS_END client=tv fixture=sinners-2025 errors=0',
  ];
  fs.writeFileSync(log, common.join('\n') + '\n');
  const run = spawnSync(process.execPath, [script, '--output', output, log], { cwd: root, encoding: 'utf8' });
  assert.equal(run.status, 0, run.stderr + run.stdout);
  const data = JSON.parse(fs.readFileSync(output, 'utf8'));
  assert.equal(data.brainVersion, 7);
  assert.equal(data.schemaVersion, 5);
  // The SHA of the actual official Nuvio client build is independent from
  // NiakVIO's commit and the provider-JS content hash. Older reports stay
  // unknown; do not infer the user-installed TV version from a native run.
  assert.equal(data.officialClientSha, '');
  const headOut = path.join(tmp, 'brain-pinned-client.json');
  const officialHead = 'c'.repeat(40);
  const pinned = spawnSync(process.execPath, [
    script, '--output', headOut, '--official-client-sha', officialHead, log,
  ], { cwd: root, encoding: 'utf8' });
  assert.equal(pinned.status, 0, pinned.stderr + pinned.stdout);
  const pinnedData = JSON.parse(fs.readFileSync(headOut, 'utf8'));
  assert.equal(pinnedData.officialClientSha, officialHead);
  assert.equal(pinnedData.readerObserved, data.readerObserved);
  assert.equal(pinnedData.evidenceComplete, data.evidenceComplete);
  const forged = spawnSync(process.execPath, [
    script, '--output', path.join(tmp, 'forged-head.json'),
    '--official-client-sha', 'https://private.invalid/SECRET', log,
  ], { cwd: root, encoding: 'utf8' });
  assert.notEqual(forged.status, 0);
  assert.equal(fs.existsSync(path.join(tmp, 'forged-head.json')), false);
  assert.equal(data.evidenceComplete, true);
  assert.equal(data.policy.evidenceUsable, true);
  assert.equal(data.policy.learningAllowed, false);
  assert.equal(data.policy.repairPlanningAllowed, false);
  assert.equal(data.policy.providerMutationRequiresCrossClientConsensus, true);
  assert.equal(data.crossClientProviderFailureGroups, 0);
  assert.equal(data.policy.providerLoadJsMutationAllowed, false);
  assert.equal(data.readerObserved, 3);
  assert.equal(data.readerHealthy, 1);
  // Android TV READY and plausible duration are not decoded playback when
  // width and height are zero. This remains an owner-unknown Brain diagnosis.
  const unverifiedLog = path.join(tmp, 'tv-video-format-unverified.log');
  const unverifiedOutput = path.join(tmp, 'tv-video-format-unverified.json');
  const unverifiedLines = common.map((line) =>
    line.startsWith('FIELD_NATIVE_PLAYER ') && line.includes(`provider64=${b64('PURSTREAM')}`)
      ? line.replace('video_width=1280 video_height=720', 'video_width=0 video_height=0')
      : line
  );
  fs.writeFileSync(unverifiedLog, unverifiedLines.join('\n') + '\n');
  spawnSync(process.execPath, [script, '--output', unverifiedOutput, unverifiedLog], {
    cwd: root, encoding: 'utf8',
  });
  const unverified = JSON.parse(fs.readFileSync(unverifiedOutput, 'utf8'));
  assert.equal(unverified.readerHealthy, 0);
  assert.equal(unverified.readerFailures, 3);
  assert.ok(unverified.observations.some((row) =>
    row.failureClass === 'playback_video_format_unverified' &&
    row.providerMutationEligible === false &&
    row.failureDomain === 'unresolved_media'
  ));
  assert.equal(data.readerFailures, 2);
  assert.equal(data.providerEligibleReaderFailures, 2);

  // Exact v35 family: production video decoded and the HLS master advertises
  // two audio languages + one subtitle. A TV audio count of zero is contradictory
  // because the Audio control had to exist for the probe to emit zero. Brain must
  // retain this as a harness observation failure, never as provider repair authority.
  const topologyLog = path.join(tmp, 'tv-track-topology-collapse.log');
  const topologyOutput = path.join(tmp, 'tv-track-topology-collapse.json');
  const topologyLines = [];
  for (const line of common) {
    if (line.startsWith('FIELD_NATIVE_PLAYER ') && line.includes(`provider64=${b64('PURSTREAM')}`)) {
      topologyLines.push(
        line.replace(
          'audio_track_count=1',
          `audio_track_count=0 audio_track_languages64=${b64('')} subtitle_track_count=-1 subtitle_track_languages64=${b64('')}`,
        ),
      );
      topologyLines.push(
        `FIELD_NATIVE_TRANSPORT client=tv fixture=sinners-2025 provider64=${b64('PURSTREAM')} request_type=movie route_mode=declared index=0 state=ok kind=hls status=200 audio_track_count=2 audio_track_languages64=${b64('fr,en')} subtitle_track_count=1 subtitle_track_languages64=${b64('fr')}`,
      );
    } else {
      topologyLines.push(line);
    }
  }
  fs.writeFileSync(topologyLog, topologyLines.join('\n') + '\n');
  spawnSync(process.execPath, [script, '--output', topologyOutput, topologyLog], {
    cwd: root, encoding: 'utf8',
  });
  const topology = JSON.parse(fs.readFileSync(topologyOutput, 'utf8'));
  const collapsed = topology.observations.find((row) =>
    row.provider === 'purstream' && row.observationLayer === 'player');
  assert.ok(collapsed);
  assert.equal(collapsed.failureClass, 'playback_audio_ui_observer_empty');
  assert.equal(collapsed.failureDomain, 'harness_observation');
  assert.equal(collapsed.providerMutationEligible, false);
  assert.equal(collapsed.playerAudioTrackCount, 0);
  assert.equal(collapsed.transportAudioTrackCount, 2);
  assert.equal(collapsed.transportAudioTrackLanguages, 'fr,en');
  assert.equal(collapsed.transportSubtitleTrackCount, 1);
  assert.equal(topology.readerHealthy, 0);
  assert.equal(topology.providerEligibleReaderFailures, 2);
  assert.equal(topology.harnessObservationReaderFailures, 1);
  assert.equal(topology.policy.productionWritesAllowed, false);

  // Multiple evidence files can contain the same client/fixture/provider/index.
  // Never let one run's HLS expectations contaminate another run's player row.
  const isolatedLog = path.join(tmp, 'tv-track-topology-isolated-second-run.log');
  const isolatedOutput = path.join(tmp, 'tv-track-topology-isolated.json');
  fs.writeFileSync(isolatedLog, common.join('\n') + '\n');
  spawnSync(process.execPath, [
    script, '--output', isolatedOutput, topologyLog, isolatedLog,
  ], { cwd: root, encoding: 'utf8' });
  const isolated = JSON.parse(fs.readFileSync(isolatedOutput, 'utf8'));
  const purstreamRows = isolated.observations.filter((row) =>
    row.provider === 'purstream' && row.observationLayer === 'player');
  assert.equal(purstreamRows.length, 2);
  assert.equal(
    purstreamRows.filter((row) => row.failureClass === 'playback_audio_ui_observer_empty').length,
    1,
  );
  assert.equal(purstreamRows.filter((row) => row.failureClass === 'healthy').length, 1);

  assert.equal(data.clientRuntimeReaderFailures, 0);
  assert.equal(data.evidenceStats.providerLoads, 2);
  assert.equal(data.evidenceStats.repositoryHttpRequests, 1);
  assert.equal(data.providerLoadIssues.length, 0);
  // Single-client failures remain useful diagnostic observations, but the policy
  // above forbids learning/repair until an independent client corroborates them.
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

  // A native 25-second timeout has no result/reader. It is still a Brain
  // outcome: retain the observed error and forbid provider mutation without
  // a proven causal owner. A later different provider must not erase it.
  const hardTimeoutLog = path.join(tmp, 'native-tv-hard-timeout.log');
  const hardTimeoutOutput = path.join(tmp, 'native-tv-hard-timeout.json');
  fs.writeFileSync(hardTimeoutLog, [
    ...common,
    `FIELD_NATIVE_ERROR client=tv fixture=sinners-2025 provider64=${b64('SADISFLIX')} request_type=movie route_mode=declared duration_ms=25000 error64=${b64('provider_hard_timeout_ms=25000')}`,
  ].join('\n') + '\n');
  spawnSync(process.execPath, [script, '--output', hardTimeoutOutput, hardTimeoutLog], {
    cwd: root, encoding: 'utf8',
  });
  const timeout = JSON.parse(fs.readFileSync(hardTimeoutOutput, 'utf8'));
  assert.equal(timeout.nativeExecutionDiagnosticObserved, 1);
  const sadisOutcome = timeout.providerOutcomes.find((row) => row.provider === 'sadisflix');
  assert.ok(sadisOutcome, 'selected native provider timeout must not disappear from Brain outcomes');
  assert.equal(sadisOutcome.nativeExecutionTimeouts, 1);
  assert.equal(sadisOutcome.failures, 1);
  assert.equal(sadisOutcome.providerEligibleFailures, 0);
  assert.equal(sadisOutcome.failureClasses.provider_hard_timeout, 1);
  assert.equal(timeout.policy.providerMutationRequiresCrossClientConsensus, true);
  assert.equal(timeout.policy.productionWritesAllowed, false);
  assert.equal(timeout.nativeExecutionDiagnostics[0].providerJsMutationAllowed, false);

  // Real NuvioTV UI selection is different from directly invoking the
  // installed JS. An omitted provider belongs to client/plugin state or the
  // manifest media-type gate, not a provider extraction repair.
  const selectionLog = path.join(tmp, 'native-tv-app-selection.log');
  const selectionOutput = path.join(tmp, 'native-tv-app-selection.json');
  const selectionFixture = common
    .filter((line) => !line.includes(`provider64=${b64('MOVIESDRIVE')}`) ||
      (!line.startsWith('FIELD_NATIVE_PLAYER ') &&
       !line.startsWith('FIELD_NATIVE_PLAYER_BEGIN ')))
    .map((line) => line.includes(`provider64=${b64('MOVIESDRIVE')}`) &&
      line.startsWith('FIELD_NATIVE_RESULT ')
      ? line.replace('count=2', 'count=0')
      : line);
  selectionFixture.splice(
    selectionFixture.findIndex((line) => line.startsWith('FIELD_NATIVE_RESULT ') &&
      line.includes(`provider64=${b64('MOVIESDRIVE')}`)),
    0,
    `FIELD_NATIVE_PROVIDER_APP_SELECTION client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} eligible=false plugins_enabled=true runtime_enabled=false manifest_enabled=true supported_type=true request_type=movie reason=scraper_disabled_locally`,
  );
  selectionFixture.push(
    `FIELD_NATIVE_PROVIDER_APP_SELECTION client=tv fixture=sinners-2025 provider64=${b64('PURSTREAM')} eligible=true plugins_enabled=true runtime_enabled=true supported_type=true request_type=movie`,
    `FIELD_NATIVE_PROVIDER_APP_SELECTION client=tv fixture=sinners-2025 provider64=${b64('PURSTREAM')} eligible=false request_type=movie reason=https://private.example/?token=SHOULD_NOT_PERSIST`,
  );
  fs.writeFileSync(selectionLog, selectionFixture.join('\n') + '\n');
  const selected = spawnSync(process.execPath, [script, '--output', selectionOutput, selectionLog], {
    cwd: root, encoding: 'utf8',
  });
  const selectionData = JSON.parse(fs.readFileSync(selectionOutput, 'utf8'));
  assert.equal(selectionData.appSelectionObserved, 2);
  assert.equal(selectionData.appSelectionObservations[0].provider, 'moviesdrive');
  assert.equal(selectionData.appSelectionObservations[0].eligible, false);
  assert.equal(selectionData.appSelectionObservations[0].runtimeEnabled, false);
  assert.equal(selectionData.appSelectionObservations[1].eligible, true);
  assert.equal(selectionData.appSelectionObservations[0].proofAuthority, false);
  assert.equal(selectionData.policy.clientSelectionProviderJsMutationAllowed, false);
  assert.doesNotMatch(JSON.stringify(selectionData.appSelectionObservations), /private\.example|SHOULD_NOT_PERSIST/);
  // An incomplete corpus may describe an app-selection observation, but must
  // never turn it into accepted Brain issue memory or a repair candidate.
  if (selectionData.evidenceComplete) {
    assert.equal(selected.status, 0, selected.stderr + selected.stdout);
    assert.equal(selectionData.appSelectionFailures, 1);
    assert.equal(selectionData.appSelectionIssues[0].failureClass, 'client_scraper_disabled_locally');
    assert.equal(selectionData.appSelectionIssues[0].providerJsMutationAllowed, false);
    assert.equal(selectionData.appSelectionIssues[0].coreOrManifestProposalAllowed, false);
    assert.equal(selectionData.policy.repositoryLearningAllowed, false);
    assert.equal(selectionData.providerLoadActionableFailures, 0);
  } else {
    assert.equal(selectionData.appSelectionIssues.length, 0);
    assert.equal(selectionData.policy.clientSelectionDiagnosticLearningAllowed, false);
  }

  // A real native zero-stream result is not a provider-JS fix instruction.
  // The transient QuickJS diagnostic contributes one sanitized, non-authorizing
  // observation to the Brain backlog, even when there is no media player.
  const jsLog = path.join(tmp, 'tv-quickjs-zero.log');
  const jsOutput = path.join(tmp, 'tv-quickjs-zero.json');
  const noMedia = common
    .filter((line) => !line.includes(`provider64=${b64('MOVIESDRIVE')}`) ||
      (!line.startsWith('FIELD_NATIVE_PLAYER ') &&
       !line.startsWith('FIELD_NATIVE_PLAYER_BEGIN ')))
    .map((line) => line.includes(`provider64=${b64('MOVIESDRIVE')}`) &&
      line.startsWith('FIELD_NATIVE_RESULT ')
      ? line.replace('count=2', 'count=0')
      : line);
  const resultAt = noMedia.findIndex((line) => line.startsWith('FIELD_NATIVE_RESULT ') &&
    line.includes(`provider64=${b64('MOVIESDRIVE')}`));
  assert.ok(resultAt >= 0);
  noMedia.splice(resultAt, 0,
    `FIELD_NATIVE_PROVIDER_APP_SELECTION client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} request_type=movie eligible=true plugins_enabled=true runtime_enabled=true manifest_enabled=true supported_type=true reason=selected`,
    `FIELD_NATIVE_QUICKJS_DIAGNOSTIC client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} phase=call category=none request_type=movie count=0`,
    `FIELD_NATIVE_QUICKJS_DIAGNOSTIC client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} phase=result category=none request_type=movie count=0`,
    `FIELD_NATIVE_QUICKJS_DIAGNOSTIC client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} phase=error category=reference_error request_type=movie count=0`,
    `FIELD_NATIVE_QUICKJS_DIAGNOSTIC client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} phase=error category=https://secret.example/token=PRIVATE request_type=movie count=0`,
  );
  fs.writeFileSync(jsLog, noMedia.join('\n') + '\n');
  const jsRun = spawnSync(process.execPath, [script, '--output', jsOutput, jsLog], {
    cwd: root, encoding: 'utf8',
  });
  const jsData = JSON.parse(fs.readFileSync(jsOutput, 'utf8'));
  assert.equal(jsData.quickJsDiagnosticObserved, 3);
  assert.equal(jsData.quickJsDiagnostics[0].phase, 'call');
  assert.equal(jsData.quickJsDiagnostics[1].phase, 'result');
  assert.equal(jsData.quickJsDiagnostics[2].category, 'reference_error');
  assert.equal(jsData.policy.quickJsDiagnosticProviderMutationAllowed, false);
  assert.doesNotMatch(JSON.stringify(jsData.quickJsDiagnostics), /secret\.example|PRIVATE/);
  assert.equal(jsData.quickJsUnverifiedObserved, 2);
  assert.equal(jsData.policy.quickJsDiagnosticLearningAllowed, true);
  assert.equal(jsData.policy.quickJsDiagnosticProviderMutationAllowed, false);
  assert.ok(jsData.observations.some((x) =>
    x.failureClass === 'native_quickjs_zero_stream' &&
    x.observationLayer === 'native_quickjs' &&
    x.providerMutationEligible === false &&
    x.nativeReaderEvidenceComplete === jsData.evidenceComplete
  ));
  // No player exists for a zero-stream provider. The runner must retain the
  // executed QuickJS failure as diagnostic evidence even when media proof is
  // intrinsically incomplete; it cannot grant repair or publication authority.
  const noReaderLog = path.join(tmp, 'tv-quickjs-no-reader.log');
  const noReaderOutput = path.join(tmp, 'tv-quickjs-no-reader.json');
  const noReaderLines = noMedia.filter((line) =>
    !line.startsWith('FIELD_NATIVE_PLAYER ') &&
    !line.startsWith('FIELD_NATIVE_PLAYER_BEGIN '));
  fs.writeFileSync(noReaderLog, noReaderLines.join('\n') + '\n');
  const noReaderRun = spawnSync(process.execPath,
    [script, '--output', noReaderOutput, noReaderLog],
    { cwd: root, encoding: 'utf8' });
  const noReaderData = JSON.parse(fs.readFileSync(noReaderOutput, 'utf8'));
  // Full trace capture can be complete even if no video player exists.
  // This field is diagnostic completeness, NEVER proof of media playback.
  assert.equal(noReaderData.evidenceComplete, true);
  assert.equal(noReaderData.readerObserved, 0);
  assert.equal(noReaderData.readerHealthy, 0);
  assert.equal(noReaderData.policy.productionWritesAllowed, false);
  assert.equal(noReaderData.policy.publicationAllowed, false);
  assert.equal(noReaderData.policy.quickJsDiagnosticProviderMutationAllowed, false);
  assert.equal(noReaderData.quickJsUnverifiedObserved, 2,
    JSON.stringify({
      app: noReaderData.appSelectionObservations?.length,
      appEligible: noReaderData.appSelectionObservations?.filter((x) => x.eligible).length,
      quick: noReaderData.quickJsDiagnostics?.length,
      quickCategories: noReaderData.quickJsDiagnostics?.map((x) => x.phase),
      extraction: noReaderData.extractionResultObserved,
      zero: noReaderData.extractionFailures,
      reader: noReaderData.readerObserved,
    }));
  assert.equal(noReaderData.policy.quickJsDiagnosticLearningAllowed, true);
  assert.equal(noReaderData.policy.quickJsDiagnosticProviderMutationAllowed, false);
  assert.ok(noReaderData.quickJsUnverifiedObservations.every((row) =>
    row.diagnosticOnly === true && row.providerMutationEligible === false
    && row.proofAuthority === false && row.nativePlaybackAuthority === false));

  // Spoofed QuickJS lines without a matching app-selected, actually-executed
  // zero-stream request must never enter the Brain diagnostic evidence.
  const unselectedLog = path.join(tmp, 'tv-quickjs-unselected.log');
  const unselectedOutput = path.join(tmp, 'tv-quickjs-unselected.json');
  fs.writeFileSync(unselectedLog, noReaderLines.filter((line) =>
    !line.startsWith('FIELD_NATIVE_PROVIDER_APP_SELECTION ')).join('\n') + '\n');
  spawnSync(process.execPath, [script, '--output', unselectedOutput, unselectedLog],
    { cwd: root, encoding: 'utf8' });
  const unselectedData = JSON.parse(fs.readFileSync(unselectedOutput, 'utf8'));
  assert.equal(unselectedData.quickJsUnverifiedObserved, 0);

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

  // The Android guest can report an unrecognized repository format while a
  // separate addon-logo request to the SAME host is DNS-blocked. This must
  // steer Brain to transport validation, not to a provider/Core patch.
  const dnsLog = path.join(tmp, 'repo-guest-dns-correlated.log');
  const dnsOutput = path.join(tmp, 'repo-guest-dns-correlated.json');
  const originalLoad = 'FIELD_NATIVE_PROVIDER_LOAD_ERROR client=tv fixture=sinners-2025';
  const logo = 'FIELD_NATIVE_ADDON_LOGO client=tv fixture=sinners-2025'
    + ' provider64=' + b64('MOVIESDRIVE')
    + ' state=error status=0 content_type64=' + b64('UnknownHostException')
    + ' host64=' + b64('raw.githubusercontent.com');
  fs.writeFileSync(dnsLog, fs.readFileSync(installFailure, 'utf8')
    .split('\n').filter(line => !line.includes('FIELD_NATIVE_REPOSITORY_HTTP_')).join('\n')
    .replace(b64('HTTP 404'), b64('Failed to parse repository: unrecognized format'))
    .replace(originalLoad, logo + '\n' + originalLoad));
  const dnsRun = spawnSync(process.execPath, [script, '--output', dnsOutput, dnsLog], {cwd: root, encoding: 'utf8'});
  assert.equal(dnsRun.status, 0, dnsRun.stderr + dnsRun.stdout);
  const dnsReport = JSON.parse(fs.readFileSync(dnsOutput, 'utf8'));
  assert.equal(dnsReport.evidenceComplete, true);
  assert.equal(dnsReport.providerLoadIssues.length, 1);
  assert.equal(dnsReport.providerLoadIssues[0].failureClass, 'provider_repository_transport_dns_correlated');
  assert.equal(dnsReport.providerLoadIssues[0].layer, 'repository_transport');
  assert.equal(dnsReport.providerLoadIssues[0].attribution, 'correlated_not_proven');
  assert.equal(dnsReport.providerLoadIssues[0].coreOrManifestProposalAllowed, false);
  assert.equal(dnsReport.providerLoadIssues[0].providerJsMutationAllowed, false);
  assert.equal(dnsReport.providerLoadPriorities[0].coreOrManifestProposalAllowed, false);
  assert.equal(dnsReport.policy.coreOrManifestLoadProposalAllowed, false);
  assert.deepEqual(dnsReport.plans, []);
  assert.equal(JSON.stringify(dnsReport).includes('raw.githubusercontent.com'), false,
    'transient repository host must never enter persisted Brain evidence');

  // A different host, or an independently observed HTTP status for the
  // manifest itself, must NOT be reclassified as a DNS fault.
  const otherLog = path.join(tmp, 'repo-guest-other-host.log');
  const otherOutput = path.join(tmp, 'repo-guest-other-host.json');
  fs.writeFileSync(otherLog, fs.readFileSync(dnsLog, 'utf8')
    .replace('host64=' + b64('raw.githubusercontent.com'), 'host64=' + b64('other.invalid')));
  const otherRun = spawnSync(process.execPath, [script, '--output', otherOutput, otherLog], {cwd: root, encoding: 'utf8'});
  assert.equal(otherRun.status, 0, otherRun.stderr + otherRun.stdout);
  const otherReport = JSON.parse(fs.readFileSync(otherOutput, 'utf8'));
  assert.equal(otherReport.providerLoadIssues[0].failureClass, 'provider_repository_load_error');
  assert.equal(otherReport.providerLoadIssues[0].coreOrManifestProposalAllowed, true);

  const httpLog = path.join(tmp, 'repo-guest-http-observed.log');
  const httpOutput = path.join(tmp, 'repo-guest-http-observed.json');
  fs.writeFileSync(httpLog, fs.readFileSync(dnsLog, 'utf8')
    + 'FIELD_NATIVE_REPOSITORY_HTTP_RESPONSE client=tv fixture=sinners-2025 kind=manifest status=404\n');
  const httpRun = spawnSync(process.execPath, [script, '--output', httpOutput, httpLog], {cwd: root, encoding: 'utf8'});
  assert.equal(httpRun.status, 0, httpRun.stderr + httpRun.stdout);
  assert.equal(JSON.parse(fs.readFileSync(httpOutput, 'utf8')).providerLoadIssues[0].failureClass,
    'provider_repository_load_error');

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

  // Preserve the *native* terminal hard timeout even when QuickJS never
  // printed a result/error. It is NOT a zero stream or proof of provider fault.
  const separateHardTimeoutLog = path.join(tmp, 'tv-hard-timeout.log');
  const separateHardTimeoutOutput = path.join(tmp, 'tv-hard-timeout.json');
  const timeoutProvider64 = b64('MOVIESDRIVE');
  const hardBase = common.filter((line) =>
    !(line.startsWith('FIELD_NATIVE_RESULT ') &&
      line.includes(`provider64=${timeoutProvider64}`)) &&
    !(line.startsWith('FIELD_NATIVE_PLAYER ') &&
      line.includes(`provider64=${timeoutProvider64}`)) &&
    !(line.startsWith('FIELD_NATIVE_PLAYER_BEGIN ') &&
      line.includes(`provider64=${timeoutProvider64}`))
  );
  const beginIndex = hardBase.findIndex((line) =>
    line.startsWith('FIELD_NATIVE_PROVIDER_BEGIN ') &&
    line.includes(`provider64=${timeoutProvider64}`));
  assert.ok(beginIndex >= 0);
  hardBase.splice(beginIndex + 1, 0,
    'FIELD_NATIVE_ERROR client=tv fixture=sinners-2025 provider64='
      + timeoutProvider64 + ' request_type=movie route_mode=declared duration_ms=25000 error64='
      + b64('provider_hard_timeout_ms=25000'));
  fs.writeFileSync(separateHardTimeoutLog, hardBase.join('\n') + '\n');
  const timed = spawnSync(process.execPath, [script, '--output', separateHardTimeoutOutput, separateHardTimeoutLog], { cwd: root, encoding: 'utf8' });
  assert.equal(timed.status, 0, timed.stderr + timed.stdout);
  const timedData = JSON.parse(fs.readFileSync(separateHardTimeoutOutput, 'utf8'));
  assert.equal(timedData.nativeExecutionDiagnosticObserved, 1);
  assert.equal(timedData.nativeExecutionDiagnostics.length, 1);
  assert.deepEqual(
    [timedData.nativeExecutionDiagnostics[0].failureClass,
     timedData.nativeExecutionDiagnostics[0].observedDurationMs,
     timedData.nativeExecutionDiagnostics[0].configuredTimeoutMs],
    ['provider_hard_timeout', 25000, 25000],
  );
  assert.equal(timedData.nativeExecutionDiagnostics[0].providerJsMutationAllowed, false);
  assert.equal(timedData.nativeExecutionDiagnostics[0].nativePlaybackAuthority, false);
  assert.equal(timedData.nativeExecutionDiagnostics[0].proofAuthority, false);
  for (const secret of ['private.example', 'Bearer', 'SECRET']) {
    assert.equal(JSON.stringify(timedData.nativeExecutionDiagnostics).includes(secret), false);
  }

  // A synthetic official QuickJS control distinguishes normal immediate
  // delivery from a lost async Promise. It is never real provider/media proof.
  const promiseLog = path.join(tmp, 'tv-promise-control.log');
  const promiseOutput = path.join(tmp, 'tv-promise-control.json');
  fs.writeFileSync(promiseLog, [
    ...common,
    'FIELD_NATIVE_TV_PROMISE_CONTROL client=tv fixture=sinners-2025 sync_count=1 async_count=0 expected=1 test_only=true provider_media=false proof_authority=false',
    'FIELD_NATIVE_TV_PROMISE_CONTROL client=tv fixture=sinners-2025 sync_count=1 async_count=1 expected=1 test_only=false provider_media=false proof_authority=false',
    'FIELD_NATIVE_TV_PROMISE_CONTROL client=tv fixture=sinners-2025 sync_count=1 async_count=1 expected=1 test_only=true provider_media=false proof_authority=true',
    'FIELD_NATIVE_TV_PROMISE_CONTROL client=tv fixture=sinners-2025 sync_count=1 async_count=1 expected=1 test_only=true provider_media=false proof_authority=false url=https://private.example/?token=SECRET',
  ].join('\n') + '\n');
  const promiseRun = spawnSync(process.execPath, [script, '--output', promiseOutput, promiseLog], { cwd: root, encoding: 'utf8' });
  assert.equal(promiseRun.status, 0, promiseRun.stderr + promiseRun.stdout);
  const promiseData = JSON.parse(fs.readFileSync(promiseOutput, 'utf8'));
  assert.equal(promiseData.quickJsPromiseControls.length, 2);
  assert.equal(promiseData.quickJsPromiseControls[0].status, 'promise_delivery_gap');
  assert.equal(promiseData.quickJsPromiseControls[1].status, 'bridge_ok');
  assert.equal(promiseData.quickJsPromiseControls[0].proofAuthority, false);
  assert.equal(promiseData.quickJsPromiseControls[0].providerJsMutationAllowed, false);
  for (const secret of ['private.example', 'SECRET', 'https://']) {
    assert.equal(JSON.stringify(promiseData.quickJsPromiseControls).includes(secret), false);
  }

  // A real TV transcript returned media while the independent HLS probe got
  // HTTP 403; READY/duration with no video format is not certified playback.
  // The Brain must learn this without persisting signed URLs or hostnames.
  const terminalLog = path.join(tmp, 'tv-terminal-probe.log');
  const terminalOutput = path.join(tmp, 'tv-terminal-probe.json');
  fs.writeFileSync(terminalLog, [
    ...common,
    'FIELD_NATIVE_TRANSPORT client=tv fixture=sinners-2025 provider64='
      + b64('MOVIESDRIVE')
      + ' request_type=movie route_mode=declared index=0 state=dead kind=hls'
      + ' status=403 extm3u=false host64=' + b64('PRIVATE.example')
      + ' url=https://PRIVATE.example/token=SECRET headers=Bearer',
    'FIELD_NATIVE_PLAYER client=tv fixture=sinners-2025 provider64='
      + b64('MOVIESDRIVE')
      + ' request_type=movie route_mode=declared index=0 state=ready'
      + ' engine=nuvio-tv-production production_surface=true failure_stage=none'
      + ' duration_seconds=1435 video_width=0 video_height=0 audio_track_count=0',
  ].join('\n') + '\n');
  const terminalRun = spawnSync(process.execPath,
    [script, '--output', terminalOutput, terminalLog],
    { cwd: root, encoding: 'utf8',
      env: { ...process.env, NIAKVIO_BRAIN_NONBLOCKING: '1' } });
  assert.equal(terminalRun.status, 0, terminalRun.stderr + terminalRun.stdout);
  const terminal = JSON.parse(fs.readFileSync(terminalOutput, 'utf8'));
  assert.equal(terminal.terminalTransportDiagnosticObserved, 1);
  const blockedHls = terminal.terminalTransportDiagnostics[0];
  assert.equal(blockedHls.httpStatus, 403);
  assert.equal(blockedHls.kind, 'hls');
  assert.equal(blockedHls.source, 'independent-terminal-transport-probe');
  assert.equal(blockedHls.provider, 'moviesdrive');
  assert.equal(blockedHls.proofAuthority, false);
  assert.equal(blockedHls.providerJsMutationAllowed, false);
  const ready = terminal.observations.find(row => row.observationLayer === 'player'
    && row.state === 'ready' && row.provider === 'moviesdrive');
  assert.equal(ready.playerVideoFormatObserved, false);
  assert.equal(ready.playerAudioTrackCount, 0);
  for (const secret of ['PRIVATE.example', 'Bearer', 'SECRET', 'https://']) {
    assert.equal(JSON.stringify(terminal.terminalTransportDiagnostics).includes(secret), false);
  }

  // The provider runtime may consume a signed HLS root twice before returning
  // rows to the app. Detect 2xx -> 403 on the exact in-memory URL, but persist
  // only a route-bound boolean pattern — never the signed URL/token.
  const oneShotLog = path.join(tmp, 'tv-one-shot-hls.log');
  const oneShotOutput = path.join(tmp, 'tv-one-shot-hls.json');
  fs.writeFileSync(oneShotLog, [
    ...common.slice(0, -1),
    `FIELD_NATIVE_PROVIDER_BEGIN client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} request_type=movie route_mode=declared`,
    'D/PluginRuntime: Fetch result: 200 OK url=https://signed.example/master.m3u8?token=SECRET bodyLen=120 bodyPreview=#EXTM3U',
    'D/PluginRuntime: Fetch result: 403 Forbidden url=https://signed.example/master.m3u8?token=SECRET bodyLen=12 bodyPreview=forbidden',
    `FIELD_NATIVE_RESULT client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} request_type=movie route_mode=declared enabled=true duration_ms=24 count=0`,
    'FIELD_NATIVE_CORPUS_END client=tv fixture=sinners-2025 errors=0',
  ].join('\n') + '\n');
  const oneShotRun = spawnSync(process.execPath,
    [script, '--output', oneShotOutput, oneShotLog],
    { cwd: root, encoding: 'utf8',
      env: { ...process.env, NIAKVIO_BRAIN_NONBLOCKING: '1' } });
  assert.equal(oneShotRun.status, 0, oneShotRun.stderr + oneShotRun.stdout);
  const oneShot = JSON.parse(fs.readFileSync(oneShotOutput, 'utf8'));
  assert.equal(oneShot.prePlayerMediaRootTransitionObserved, 1);
  assert.equal(oneShot.prePlayerMediaRootTransitions.length, 1);
  assert.equal(oneShot.prePlayerFetchHostOutcomeObserved, 2);
  assert.equal(oneShot.prePlayerFetchHostOutcomes.length, 2);
  assert.deepEqual(
    oneShot.prePlayerFetchHostOutcomes.map((row) =>
      [row.kind, row.host, row.httpStatus]),
    [['hls', '', 200], ['hls', '', 403]],
  );
  const transition = oneShot.prePlayerMediaRootTransitions[0];
  assert.deepEqual(
    [transition.provider, transition.fixture, transition.requestType,
     transition.kind, transition.pattern, transition.phase],
    ['moviesdrive', 'sinners-2025', 'movie', 'hls',
     'same_media_root_2xx_then_403', 'provider-runtime-pre-player'],
  );
  assert.equal(transition.proofAuthority, false);
  assert.equal(transition.providerJsMutationAllowed, false);
  for (const secret of ['signed.example', 'SECRET', 'token=', 'https://']) {
    assert.equal(JSON.stringify(oneShot.prePlayerMediaRootTransitions).includes(secret), false);
    assert.equal(JSON.stringify(oneShot.prePlayerFetchHostOutcomes).includes(secret), false);
  }

  // A completed zero near the shared 25s JS deadline *after* a successful
  // HLS playlist is a causal routing clue, not proof of owner/playable media.
  // The root URL/token must only exist in the in-memory native log parser.
  const budgetHlsLog = path.join(tmp, 'tv-hls-near-budget.log');
  const budgetHlsOutput = path.join(tmp, 'tv-hls-near-budget.json');
  fs.writeFileSync(budgetHlsLog, [
    ...common.slice(0, -1),
    `FIELD_NATIVE_PROVIDER_BEGIN client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} request_type=movie route_mode=declared`,
    'D/PluginRuntime: Fetch result: 200 OK url=https://signed.example/master.m3u8?token=NEVER_PERSIST bodyLen=120 bodyPreview=#EXTM3U',
    `FIELD_NATIVE_RESULT client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} request_type=movie route_mode=declared enabled=true duration_ms=25477 count=0`,
    'FIELD_NATIVE_CORPUS_END client=tv fixture=sinners-2025 errors=0',
  ].join('\n') + '\n');
  const budgetRun = spawnSync(process.execPath,
    [script, '--output', budgetHlsOutput, budgetHlsLog],
    { cwd: root, encoding: 'utf8',
      env: { ...process.env, NIAKVIO_BRAIN_NONBLOCKING: '1' } });
  assert.equal(budgetRun.status, 0, budgetRun.stderr + budgetRun.stdout);
  const budgetRows = JSON.parse(fs.readFileSync(budgetHlsOutput, 'utf8'));
  assert.equal(budgetRows.prePlayerMediaRootTransitionObserved, 1);
  const budgetRow = budgetRows.prePlayerMediaRootTransitions[0];
  assert.deepEqual([budgetRow.provider, budgetRow.fixture, budgetRow.requestType,
    budgetRow.kind, budgetRow.pattern, budgetRow.phase],
  ['moviesdrive', 'sinners-2025', 'movie', 'hls',
    'hls_playlist_2xx_near_25s_zero_preplayer', 'provider-runtime-pre-player']);
  assert.equal(budgetRow.proofAuthority, false);
  assert.equal(budgetRow.publicationAuthority, false);
  assert.equal(budgetRow.nativePlaybackAuthority, false);
  assert.equal(budgetRow.providerJsMutationAllowed, false);
  for (const secret of ['signed.example', 'NEVER_PERSIST', 'token=', 'https://']) {
    assert.equal(JSON.stringify(budgetRows.prePlayerMediaRootTransitions).includes(secret), false);
  }
  // A fast zero, an actual stream, or a failed playlist must NOT trigger this
  // near-budget signal, preventing mere status/URL promotion.
  for (const [suffix, duration, count, httpStatus] of [
    ['fast-zero', 500, 0, 200],
    ['near-positive', 25477, 1, 200],
    ['near-failed-hls', 25477, 0, 403],
  ]) {
    const variantLog = path.join(tmp, 'tv-hls-' + suffix + '.log');
    const variantOutput = path.join(tmp, 'tv-hls-' + suffix + '.json');
    fs.writeFileSync(variantLog, [
      ...common.slice(0, -1),
      `FIELD_NATIVE_PROVIDER_BEGIN client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} request_type=movie route_mode=declared`,
      `D/PluginRuntime: Fetch result: ${httpStatus} url=https://signed.example/master.m3u8?token=SECRET bodyLen=0`,
      `FIELD_NATIVE_RESULT client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} request_type=movie route_mode=declared enabled=true duration_ms=${duration} count=${count}`,
      'FIELD_NATIVE_CORPUS_END client=tv fixture=sinners-2025 errors=0',
    ].join('\n') + '\n');
    const run = spawnSync(process.execPath, [script, '--output', variantOutput, variantLog],
      { cwd: root, encoding: 'utf8',
        env: { ...process.env, NIAKVIO_BRAIN_NONBLOCKING: '1' } });
    assert.equal(run.status, 0, suffix + ': ' + run.stderr + run.stdout);
    assert.equal(JSON.parse(fs.readFileSync(variantOutput, 'utf8'))
      .prePlayerMediaRootTransitions.length, 0, suffix);
  }

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