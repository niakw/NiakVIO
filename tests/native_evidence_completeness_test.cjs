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

  const collapsedMultiAudio = writeLog(tmp, 'multi-audio-collapsed.log', baseEvidence([
    'FIELD_NATIVE_PROVIDER_BEGIN client=tv fixture=sinners-2025 provider=test request_type=movie',
    'FIELD_NATIVE_RESULT client=tv fixture=sinners-2025 provider=test request_type=movie returned=1',
    'FIELD_NATIVE_PLAYER_BEGIN client=tv fixture=sinners-2025 provider=test request_type=movie index=0',
    'FIELD_NATIVE_PLAYER client=tv fixture=sinners-2025 provider=test request_type=movie index=0 state=ready audio_track_count=1',
    'FIELD_NATIVE_TRANSPORT client=tv fixture=sinners-2025 provider=test request_type=movie index=0 state=ok kind=hls audio_track_count=2',
  ], [
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=provider-loading',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=provider-result',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=player-start',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=player-result',
  ]));
  const collapsedAssessment = assessNativeEvidence([collapsedMultiAudio]);
  assert.equal(collapsedAssessment.complete, false, 'multi-audio master collapsed to one player track must fail');
  assert.ok(
    collapsedAssessment.problems.some((row) => row.startsWith('multi_audio_player_collapsed:tv:sinners-2025:test:0:')),
    `missing multi-audio collapse problem: ${JSON.stringify(collapsedAssessment.problems)}`,
  );
  assert.equal(collapsedAssessment.stats.multiAudioExpected, 1);
  assert.equal(collapsedAssessment.stats.multiAudioVerified, 0);

  const languageCollapsedMultiAudio = writeLog(tmp, 'multi-audio-language-collapsed.log', baseEvidence([
    'FIELD_NATIVE_PROVIDER_BEGIN client=tv fixture=sinners-2025 provider=test request_type=movie',
    'FIELD_NATIVE_RESULT client=tv fixture=sinners-2025 provider=test request_type=movie returned=1',
    'FIELD_NATIVE_PLAYER_BEGIN client=tv fixture=sinners-2025 provider=test request_type=movie index=0',
    'FIELD_NATIVE_PLAYER client=tv fixture=sinners-2025 provider=test request_type=movie index=0 state=ready audio_track_count=2 audio_track_languages64=ZW4',
    'FIELD_NATIVE_TRANSPORT client=tv fixture=sinners-2025 provider=test request_type=movie index=0 state=ok kind=hls audio_track_count=2 audio_track_languages64=ZW4sZnI',
  ], [
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=provider-loading',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=provider-result',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=player-start',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=player-result',
  ]));
  const languageCollapsedAssessment = assessNativeEvidence([languageCollapsedMultiAudio]);
  assert.equal(languageCollapsedAssessment.complete, false, 'matching track counts with a missing language must fail');
  assert.ok(
    languageCollapsedAssessment.problems.some((row) => row.startsWith('multi_audio_language_observation_missing:tv:sinners-2025:test:0:')),
    `missing multi-audio language collapse problem: ${JSON.stringify(languageCollapsedAssessment.problems)}`,
  );
  assert.equal(languageCollapsedAssessment.stats.multiAudioExpected, 1);
  assert.equal(languageCollapsedAssessment.stats.multiAudioVerified, 1);
  assert.equal(languageCollapsedAssessment.stats.multiAudioLanguageExpected, 1);
  assert.equal(languageCollapsedAssessment.stats.multiAudioLanguageVerified, 0);

  const preservedMultiAudio = writeLog(tmp, 'multi-audio-preserved.log', baseEvidence([
    'FIELD_NATIVE_PROVIDER_BEGIN client=tv fixture=sinners-2025 provider=test request_type=movie',
    'FIELD_NATIVE_RESULT client=tv fixture=sinners-2025 provider=test request_type=movie returned=1',
    'FIELD_NATIVE_PLAYER_BEGIN client=tv fixture=sinners-2025 provider=test request_type=movie index=0',
    'FIELD_NATIVE_PLAYER client=tv fixture=sinners-2025 provider=test request_type=movie index=0 state=ready audio_track_count=2',
    'FIELD_NATIVE_TRANSPORT client=tv fixture=sinners-2025 provider=test request_type=movie index=0 state=ok kind=hls audio_track_count=2',
  ], [
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=provider-loading',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=provider-result',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=player-start',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=player-result',
  ]));
  const preservedAssessment = assessNativeEvidence([preservedMultiAudio]);
  assert.equal(
    preservedAssessment.complete,
    true,
    `two-track master must remain multi-audio in production player: ${JSON.stringify(preservedAssessment.problems)}`,
  );
  assert.equal(preservedAssessment.stats.multiAudioExpected, 1);
  assert.equal(preservedAssessment.stats.multiAudioVerified, 1);

  const variantLowCoherent = writeLog(tmp, 'variant-low-coherent.log', baseEvidence([
    'FIELD_NATIVE_PROVIDER_BEGIN client=tv fixture=sinners-2025 provider=test request_type=movie',
    'FIELD_NATIVE_RESULT client=tv fixture=sinners-2025 provider=test request_type=movie returned=1',
    'FIELD_NATIVE_PLAYER_BEGIN client=tv fixture=sinners-2025 provider=test request_type=movie index=0',
    'FIELD_NATIVE_PLAYER client=tv fixture=sinners-2025 provider=test request_type=movie index=0 state=ready advertised_quality64=QWRhcHRpdmU video_height=540 audio_track_count=1 audio_track_languages64=aGk subtitle_track_count=1 subtitle_track_languages64=ZnI',
    'FIELD_NATIVE_TRANSPORT client=tv fixture=sinners-2025 provider=test request_type=movie index=0 state=ok kind=hls audio_track_count=4 audio_track_languages64=aGksZW4sZnIsZXM subtitle_track_count=2 subtitle_track_languages64=ZnIsZW4 audio_variant_matrix64=NTQwOmhpOzcyMDpoaXxlbnxmcnxlcw subtitle_variant_matrix64=NTQwOmZyOzcyMDpmcnxlbg',
  ], [
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=provider-loading',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=provider-result',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=player-start',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=player-result',
  ]));
  const variantLowAssessment = assessNativeEvidence([variantLowCoherent]);
  assert.equal(variantLowAssessment.complete, true, JSON.stringify(variantLowAssessment.problems));

  const variantHighCollapsed = writeLog(tmp, 'variant-high-collapsed.log', baseEvidence([
    'FIELD_NATIVE_PROVIDER_BEGIN client=tv fixture=sinners-2025 provider=test request_type=movie',
    'FIELD_NATIVE_RESULT client=tv fixture=sinners-2025 provider=test request_type=movie returned=1',
    'FIELD_NATIVE_PLAYER_BEGIN client=tv fixture=sinners-2025 provider=test request_type=movie index=0',
    'FIELD_NATIVE_PLAYER client=tv fixture=sinners-2025 provider=test request_type=movie index=0 state=ready advertised_quality64=QWRhcHRpdmU video_height=720 audio_track_count=1 audio_track_languages64=aGk subtitle_track_count=1 subtitle_track_languages64=ZnI',
    'FIELD_NATIVE_TRANSPORT client=tv fixture=sinners-2025 provider=test request_type=movie index=0 state=ok kind=hls audio_track_count=4 audio_track_languages64=aGksZW4sZnIsZXM subtitle_track_count=2 subtitle_track_languages64=ZnIsZW4 audio_variant_matrix64=NTQwOmhpOzcyMDpoaXxlbnxmcnxlcw subtitle_variant_matrix64=NTQwOmZyOzcyMDpmcnxlbg',
  ], [
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=provider-loading',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=provider-result',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=player-start',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=player-result',
  ]));
  const variantHighAssessment = assessNativeEvidence([variantHighCollapsed]);
  assert.equal(variantHighAssessment.complete, false);
  assert.ok(variantHighAssessment.problems.some((row) => row.startsWith('multi_audio_player_collapsed:')));
  assert.ok(variantHighAssessment.problems.some((row) => row.startsWith('integrated_subtitle_player_collapsed:')));

  const fixed4kMismatch = writeLog(tmp, 'fixed-4k-mismatch.log', baseEvidence([
    'FIELD_NATIVE_PROVIDER_BEGIN client=tv fixture=sinners-2025 provider=test request_type=movie',
    'FIELD_NATIVE_RESULT client=tv fixture=sinners-2025 provider=test request_type=movie returned=1',
    'FIELD_NATIVE_PLAYER_BEGIN client=tv fixture=sinners-2025 provider=test request_type=movie index=0',
    'FIELD_NATIVE_PLAYER client=tv fixture=sinners-2025 provider=test request_type=movie index=0 state=ready advertised_quality64=MjE2MHA video_height=720 audio_track_count=1 subtitle_track_count=0',
    'FIELD_NATIVE_TRANSPORT client=tv fixture=sinners-2025 provider=test request_type=movie index=0 state=ok kind=hls audio_track_count=1 subtitle_track_count=0',
  ], [
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=provider-loading',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=provider-result',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=player-start',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=player-result',
  ]));
  const fixed4kAssessment = assessNativeEvidence([fixed4kMismatch]);
  assert.equal(fixed4kAssessment.complete, false);
  assert.ok(fixed4kAssessment.problems.some((row) => row.startsWith('fixed_quality_player_mismatch:')));

  const adaptive720 = writeLog(tmp, 'adaptive-720.log', baseEvidence([
    'FIELD_NATIVE_PROVIDER_BEGIN client=tv fixture=sinners-2025 provider=test request_type=movie',
    'FIELD_NATIVE_RESULT client=tv fixture=sinners-2025 provider=test request_type=movie returned=1',
    'FIELD_NATIVE_PLAYER_BEGIN client=tv fixture=sinners-2025 provider=test request_type=movie index=0',
    'FIELD_NATIVE_PLAYER client=tv fixture=sinners-2025 provider=test request_type=movie index=0 state=ready advertised_quality64=QWRhcHRpdmU video_height=720 audio_track_count=1 subtitle_track_count=0',
    'FIELD_NATIVE_TRANSPORT client=tv fixture=sinners-2025 provider=test request_type=movie index=0 state=ok kind=hls audio_track_count=1 subtitle_track_count=0',
  ], [
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=provider-loading',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=provider-result',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=player-start',
    'FIELD_NATIVE_FRONTEND_CAPTURE client=tv fixture=sinners-2025 phase=player-result',
  ]));
  const adaptiveAssessment = assessNativeEvidence([adaptive720]);
  assert.equal(adaptiveAssessment.complete, true, JSON.stringify(adaptiveAssessment.problems));

  console.log('native evidence completeness execution-floor, quality and variant track tests passed');
} finally {
  fs.rmSync(tmp, { recursive: true, force: true });
}
