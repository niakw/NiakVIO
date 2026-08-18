#!/usr/bin/env node
import fs from "node:fs";
import process from "node:process";
import { BRAIN_CONTROL_PLANE_VERSION, classifyFailure, planRepair } from "../src/repair-brain.mjs";
import { evidenceSignature } from "../src/recipe-memory.mjs";

let input;
try {
  input = JSON.parse(fs.readFileSync(0, "utf8") || "{}");
} catch (_error) {
  process.stderr.write("brain_planner_input_invalid\n");
  process.exit(2);
}

const policy = asRecord(input.policy);
const production = asRecord(policy.production);
const maturity = asRecord(policy.skillMaturity);
const learnedSkills = normalizeLearnedSkills(input.learnedSkills);
const output = {
  schemaVersion: 3,
  brainVersion: BRAIN_CONTROL_PLANE_VERSION,
  mode: stringValue(input.mode, "quick"),
  plannerErrors: 0,
  plans: {},
};

for (const rawItem of asArray(input.items)) {
  const item = asRecord(rawItem);
  const key = stringValue(item.key);
  if (!key) continue;
  try {
    output.plans[key] = buildPlan(item);
  } catch (error) {
    output.plannerErrors += 1;
    output.plans[key] = deferredPlannerError(item, error);
  }
}

process.stdout.write(JSON.stringify(output));

function buildPlan(item) {
  const candidate = asRecord(item.candidate);
  const result = asRecord(item.result);
  const state = asRecord(item.state);
  const evidence = deriveEvidence(candidate, result);
  evidence.failureClass = classifyFailure(evidence);
  const signature = evidenceSignature(evidence);
  const providerId = stringValue(candidate.canonical_id ?? candidate.upstream_id).toLowerCase();
  const reusable = learnedSkills
    .filter((skill) => !skill.failureClass || skill.failureClass === evidence.failureClass || skill.failure_class === evidence.failureClass)
    .filter((skill) => {
      const providers = stringArray(skill.providers ?? skill.provenOnProviders);
      return skill.autoApply === true || providers.map((value) => value.toLowerCase()).includes(providerId);
    })
    .map((skill) => ({
      id: stringValue(skill.id),
      failureClass: skill.failureClass ?? skill.failure_class ?? null,
      capabilities: stringArray(skill.capabilities),
      actions: stringArray(skill.actions).length ? stringArray(skill.actions) : [`apply learned profile ${stringValue(skill.profile)}`],
      profile: stringValue(skill.profile) || null,
      learned: true,
      maturity: stringValue(skill.maturity, "experimental"),
    }))
    .filter((skill) => skill.id);

  const signatureCounts = asRecord(state.signatureCounts);
  const repeatedSignatureCount = finiteNumber(
    signatureCounts[signature],
    finiteNumber(state.repeatedSignatureCount, 0),
  );
  const plan = planRepair(evidence, {
    signature,
    learnedSkills: reusable,
    maxHypotheses: finiteNumber(production.maxHypotheses, 3),
    budget: {
      maxHypotheses: finiteNumber(production.maxHypotheses, 3),
      maxMutations: finiteNumber(production.maxMutationsPerProvider, 2),
      maxRepeatedSignature: finiteNumber(production.maxRepeatedSignature, 2),
      maxGeneratedBytes: finiteNumber(production.maxGeneratedBytesPerProvider, 180000),
      maxElapsedMs: finiteNumber(production.maxElapsedMsPerProvider, 45000),
      mutationCount: finiteNumber(state.mutationCount, 0),
      repeatedSignatureCount,
      generatedBytes: finiteNumber(state.generatedBytes, 0),
      elapsedMs: finiteNumber(state.elapsedMs, 0),
    },
    learningLab: stringValue(input.mode) === "learning",
    coreMutationRequested: state.coreMutationRequested === true,
  });
  const hypotheses = asArray(plan.hypotheses).filter(isRecord);
  return {
    brainVersion: finiteNumber(plan.brainVersion, BRAIN_CONTROL_PLANE_VERSION),
    providerId,
    failureClass: stringValue(plan.failureClass, "unknown_failure"),
    signature,
    action: stringValue(plan.action, "deferred_retry"),
    exitReason: plan.exitReason ?? null,
    hypotheses: hypotheses.map((row) => ({
      id: stringValue(row.id),
      capabilities: stringArray(row.capabilities),
      actions: stringArray(row.actions),
      learned: row.learned === true,
      maturity: row.maturity ?? null,
    })).filter((row) => row.id),
    allowedProfiles: profilesForPlan({ ...plan, hypotheses }, reusable),
    budget: asRecord(plan.budget),
    fallbackPolicy: stringValue(plan.fallbackPolicy, "lkg_only_after_repair_budget"),
    coreMutationPolicy: stringValue(plan.coreMutationPolicy, "proposal_only"),
    skillPolicy: maturity,
    evidenceSource: nativePlayerEvidence(result) ? "official_native_reader" : "runtime_health",
  };
}

function deferredPlannerError(item, error) {
  const candidate = asRecord(item.candidate);
  return {
    brainVersion: BRAIN_CONTROL_PLANE_VERSION,
    providerId: stringValue(candidate.canonical_id ?? candidate.upstream_id).toLowerCase(),
    failureClass: "unknown_failure",
    signature: null,
    action: "deferred_retry",
    exitReason: "planner_item_error",
    hypotheses: [],
    allowedProfiles: [],
    budget: policyBudget(),
    fallbackPolicy: "lkg_only_after_repair_budget",
    coreMutationPolicy: "proposal_only",
    skillPolicy: maturity,
    plannerErrorClass: safeErrorClass(error),
  };
}

function policyBudget() {
  return {
    maxHypotheses: finiteNumber(production.maxHypotheses, 3),
    maxMutations: finiteNumber(production.maxMutationsPerProvider, 2),
    maxRepeatedSignature: finiteNumber(production.maxRepeatedSignature, 2),
    maxGeneratedBytes: finiteNumber(production.maxGeneratedBytesPerProvider, 180000),
    maxElapsedMs: finiteNumber(production.maxElapsedMsPerProvider, 45000),
  };
}

function normalizeLearnedSkills(value) {
  if (Array.isArray(value)) return value.filter(isRecord);
  if (isRecord(value)) return Object.values(value).filter(isRecord);
  return [];
}

function profilesForPlan(plan, learned) {
  if (stringValue(plan.action) !== "probe-targeted-repair") return [];
  const hypotheses = asArray(plan.hypotheses).filter(isRecord);
  const hypothesisIds = new Set(hypotheses.map((row) => stringValue(row.id)).filter(Boolean));
  const profiles = [];
  for (const skill of learned) {
    const profile = stringValue(skill.profile);
    if (profile && hypothesisIds.has(stringValue(skill.id))) profiles.push(profile);
  }
  const map = {
    "rediscover-search-route": ["adaptive_runtime_recovery"],
    "repair-search-parser": ["dle_html_search_recovery", "adaptive_runtime_recovery"],
    "repair-detail-resolution": ["adaptive_runtime_recovery"],
    "repair-series-navigation": ["adaptive_runtime_recovery"],
    "repair-anime-episode-mapping": ["adaptive_runtime_recovery"],
    "discover-player-chain": ["adaptive_runtime_recovery"],
    "capture-media-network": ["adaptive_runtime_recovery"],
    "inspect-player-javascript": ["adaptive_runtime_recovery"],
    "preserve-playback-context": ["adaptive_runtime_recovery"],
    "refresh-media-token": ["adaptive_runtime_recovery"],
    "validate-final-media": ["adaptive_runtime_recovery"],
    "bootstrap-session": ["adaptive_runtime_recovery"],
    "alternate-official-route": ["adaptive_runtime_recovery"],
    "resolve-terminal-media-for-reader": ["adaptive_runtime_recovery"],
    "select-reader-compatible-source": ["adaptive_runtime_recovery"],
    "refresh-malformed-media": ["adaptive_runtime_recovery"],
    "repair-adaptive-manifest": ["adaptive_runtime_recovery"],
    "select-decodable-source": ["adaptive_runtime_recovery"],
    "prefer-cross-engine-compatible-source": ["adaptive_runtime_recovery"],
  };
  for (const hypothesis of hypotheses) {
    for (const profile of map[stringValue(hypothesis.id)] ?? []) profiles.push(profile);
  }
  return [...new Set(profiles)];
}

function deriveEvidence(candidate, result) {
  const status = stringValue(result.status, "runtime_error");
  const tests = asArray(result.tests).filter(isRecord);
  const evidence = asRecord(result.evidence);
  const playable = finiteNumber(evidence.streams_playable, maxNumber(tests.map((row) => row.streams_playable)));
  const returned = finiteNumber(evidence.streams_returned, maxNumber(tests.map((row) => row.stream_count ?? row.streams_returned)));
  const failureText = tests.map((row) => {
    const details = asRecord(row.error_details);
    return `${stringValue(row.failure_class)} ${stringValue(row.status)} ${stringValue(details.code)} ${stringValue(details.message)}`;
  }).join(" ").toLowerCase();
  const observations = tests.flatMap((row) => asArray(row.network_observations).filter(isRecord));
  const statuses = observations.map((row) => Number(row.status)).filter(Number.isFinite);
  const providerStatuses = observations.filter((row) => row.infrastructure !== true).map((row) => Number(row.status)).filter(Number.isFinite);
  const blocked = providerStatuses.find((code) => [401, 403, 407, 429, 451].includes(code));
  const gone = providerStatuses.find((code) => [404, 410].includes(code));
  const fixture = asRecord(tests[0]?.fixture);
  const metadata = asRecord(candidate.metadata);
  const supportedTypes = stringArray(metadata.supportedTypes);
  const mediaType = stringValue(fixture.category ?? fixture.mediaType ?? supportedTypes[0], "movie").toLowerCase();
  const identityContradiction = finiteNumber(evidence.identity_contradiction_count, 0) > 0 || finiteNumber(evidence.duration_identity_mismatch_count, 0) > 0 || /identity|duration.*mismatch/.test(failureText);
  const invoked = !/not[_ -]?invoked|invalid[_ -]?request[_ -]?argument|object%20object|object object/.test(failureText);
  const contractDrift = status === "runtime_error" && /invalid[_ -]?request[_ -]?argument|object%20object|object object|signature|argument/.test(failureText);

  const native = nativePlayerEvidence(result);
  if (native) {
    return {
      invoked: true,
      request: { mediaType },
      playableStreams: 0,
      stages: {
        playerPlayback: {
          attempted: true,
          sourceStatus: native.sourceStatus,
          sourceSignature: native.sourceSignature,
          exoReady: native.exoReady,
          exoCode: native.exoCode,
          mpvReady: native.mpvReady,
          playable: native.playable,
        },
      },
    };
  }

  if (playable > 0 && !identityContradiction) {
    return { invoked, contractDrift, playableStreams: playable, request: { mediaType }, stages: { validation: { attempted: true, playable: true, playableCount: playable, statuses } } };
  }
  if (identityContradiction) return { invoked, suspicious: true, request: { mediaType } };
  if (status === "provider_unreachable" && /dns|enotfound|eai_again|getaddrinfo/.test(failureText)) {
    return { invoked, dns: { ok: false }, request: { mediaType } };
  }
  if (status === "blocked" || blocked) {
    return { invoked, dns: { ok: true }, request: { mediaType }, stages: { homepage: { status: blocked || 403 } } };
  }
  if (returned > 0) {
    return {
      invoked, contractDrift, request: { mediaType }, playableStreams: 0,
      stages: {
        player: { attempted: true, found: true },
        media: { attempted: true, found: true, streamCount: returned },
        validation: { attempted: true, observed: true, playable: false, playableCount: 0, statuses: statuses.length ? statuses : [gone || 200] },
      },
    };
  }
  if (/episode/.test(failureText)) {
    return { invoked, request: { mediaType: mediaType === "movie" ? "tv" : mediaType }, stages: { search: { attempted: true, status: 200, matches: 1 }, identity: { attempted: true, matched: true }, detail: { attempted: true, found: true }, episode: { attempted: true, found: false } } };
  }
  if (/player|iframe|embed/.test(failureText)) {
    return { invoked, request: { mediaType }, stages: { player: { attempted: true, found: false } } };
  }
  if (/media|stream|hls|dash|m3u8|mp4/.test(failureText) && !/no[_ -]?streams?/.test(failureText)) {
    return { invoked, request: { mediaType }, stages: { player: { attempted: true, found: true }, media: { attempted: true, found: false } } };
  }
  if (gone || /provider_http_error|404|410|no[_ -]?streams?|runtime_empty/.test(failureText) || ["no_streams", "reachable", "degraded", "unavailable", "provider_unreachable"].includes(status)) {
    return { invoked, request: { mediaType }, stages: { search: { attempted: true, status: gone || 200, matches: 0 } } };
  }
  return { invoked, contractDrift, request: { mediaType }, playableStreams: 0 };
}

function nativePlayerEvidence(result) {
  const tests = asArray(result.tests).filter(isRecord);
  const row = tests.find((test) => stringValue(test.status) === "native_player_failure" || stringValue(test.failure_class).startsWith("player_") || stringValue(test.failure_class) === "media_extraction_gap" || stringValue(test.failure_class) === "playback_context_gap");
  if (!row) return null;
  const details = asRecord(row.error_details);
  const message = stringValue(details.message).toLowerCase();
  const failureClass = stringValue(row.failure_class);
  const exoCode = numericToken(message, "exo_code") || finiteNumber(details.code, 0) || exoCodeFromName(stringValue(details.code));
  const sourceStatus = numericToken(message, "source_status") || firstStatus(row.network_observations);
  const sourceSignature = stringToken(message, "signature") || (
    failureClass === "media_extraction_gap" ? "html" : "unknown"
  );
  const mpvReady = booleanToken(message, "mpv_ready");
  const exoReady = booleanToken(message, "exo_ready");
  const playable = booleanToken(message, "playable");
  return {
    sourceStatus,
    sourceSignature,
    exoCode,
    exoReady,
    mpvReady,
    playable,
  };
}

function exoCodeFromName(value) {
  const name = String(value || "");
  const map = {
    ERROR_CODE_PARSING_CONTAINER_MALFORMED: 3001,
    ERROR_CODE_PARSING_MANIFEST_MALFORMED: 3002,
    ERROR_CODE_PARSING_CONTAINER_UNSUPPORTED: 3003,
    ERROR_CODE_PARSING_MANIFEST_UNSUPPORTED: 3004,
    ERROR_CODE_DECODING_FAILED: 4003,
    ERROR_CODE_DECODING_FORMAT_EXCEEDS_CAPABILITIES: 4004,
    ERROR_CODE_DECODING_FORMAT_UNSUPPORTED: 4005,
  };
  return map[name] || 0;
}
function numericToken(text, name) {
  const match = new RegExp(`(?:^|\\s)${name}=(-?[0-9]+)(?:\\s|$)`).exec(String(text || ""));
  return match ? finiteNumber(match[1], 0) : 0;
}
function stringToken(text, name) {
  const match = new RegExp(`(?:^|\\s)${name}=([a-z0-9_.:-]+)(?:\\s|$)`).exec(String(text || ""));
  return match ? match[1] : "";
}
function booleanToken(text, name) {
  const match = new RegExp(`(?:^|\\s)${name}=(true|false)(?:\\s|$)`).exec(String(text || ""));
  return match?.[1] === "true";
}
function firstStatus(value) {
  for (const row of asArray(value).filter(isRecord)) {
    const status = Number(row.status);
    if (Number.isFinite(status)) return status;
  }
  return 0;
}

function asRecord(value) {
  return isRecord(value) ? value : {};
}
function isRecord(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}
function asArray(value) {
  return Array.isArray(value) ? value : [];
}
function stringArray(value) {
  if (Array.isArray(value)) return value.map((item) => stringValue(item)).filter(Boolean);
  const scalar = stringValue(value);
  return scalar ? [scalar] : [];
}
function stringValue(value, fallback = "") {
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return fallback;
}
function finiteNumber(value, fallback = 0) {
  const number = Number(value);
  return Number.isFinite(number) ? number : Number(fallback) || 0;
}
function maxNumber(values) {
  const numbers = values.map(Number).filter(Number.isFinite);
  return numbers.length ? Math.max(0, ...numbers) : 0;
}
function safeErrorClass(error) {
  const name = stringValue(error?.name, "Error");
  return /^[A-Za-z0-9_.-]{1,64}$/.test(name) ? name : "Error";
}
