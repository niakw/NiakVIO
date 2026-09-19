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
const globalSkillConfig = readJsonFile("engine_v2/config/global-repair-skills.json", {});
const coreRepairConfig = readJsonFile("engine_v2/config/core-repair-types.json", {});
const providerOverrides = readJsonFile("provider-overrides.json", {});
const learningMode = stringValue(input.mode, "quick") === "learning";
const learnedSkills = learningMode
  ? [
      ...normalizeLearnedSkills(input.learnedSkills),
      ...normalizeLearnedSkills(asRecord(globalSkillConfig).skills),
    ]
  : [];
const runtimeCompatibility = buildRuntimeCompatibility(
  readJsonFile("automation/nuvio-client-compatibility-matrix.json", {}),
);
const output = {
  schemaVersion: 2,
  brainVersion: BRAIN_CONTROL_PLANE_VERSION,
  mode: stringValue(input.mode, "quick"),
  plannerErrors: 0,
  runtimeCompatibility: {
    matrixVersion: runtimeCompatibility.matrixVersion,
    supportedCapabilities: runtimeCompatibility.supportedCapabilities,
    invalidCapabilities: runtimeCompatibility.invalidCapabilities,
    clients: runtimeCompatibility.clients,
  },
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
  const capabilityStrategy = stringValue(asRecord(asRecord(providerOverrides.provider_capabilities)[providerId]).strategy, "unknown").toLowerCase();
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
      clientVersions: asRecord(skill.clientVersions ?? skill.runtimeVersions),
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
    runtimeCompatibility,
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
  const repairTarget = resolveRepairTarget(plan.failureClass, capabilityStrategy, evidence.observedPipelineStage, stringValue(input.mode, "quick"));
  return {
    brainVersion: finiteNumber(plan.brainVersion, BRAIN_CONTROL_PLANE_VERSION),
    providerId,
    failureClass: stringValue(plan.failureClass, "unknown_failure"),
    repairScope: repairTarget.scope,
    repairType: repairTarget.repairType,
    repairEngine: repairTarget.engine,
    pipelineStage: repairTarget.pipelineStage,
    observedPipelineStage: stringValue(evidence.observedPipelineStage, "unknown"),
    learningDisposition: repairTarget.learningDisposition,
    capabilityStrategy,
    signature,
    action: stringValue(plan.action, "deferred_retry"),
    exitReason: plan.exitReason ?? null,
    hypotheses: hypotheses.map((row) => ({
      id: stringValue(row.id),
      capabilities: stringArray(row.capabilities),
      clientVersions: asRecord(row.clientVersions ?? row.runtimeVersions),
      actions: stringArray(row.actions),
      learned: row.learned === true,
      maturity: row.maturity ?? null,
    })).filter((row) => row.id),
    allowedProfiles: profilesForRepairTarget({ ...plan, hypotheses }, repairTarget),
    budget: asRecord(plan.budget),
    fallbackPolicy: stringValue(plan.fallbackPolicy, "lkg_only_after_repair_budget"),
    coreMutationPolicy: stringValue(plan.coreMutationPolicy, "proposal_only"),
    skillPolicy: maturity,
  };
}

function deferredPlannerError(item, error) {
  const candidate = asRecord(item.candidate);
  const learningMode = stringValue(input.mode, "quick") === "learning";
  return {
    brainVersion: BRAIN_CONTROL_PLANE_VERSION,
    providerId: stringValue(candidate.canonical_id ?? candidate.upstream_id).toLowerCase(),
    failureClass: "unknown_failure",
    repairScope: learningMode ? "learning" : "deferred",
    repairType: "architecture_gap",
    repairEngine: learningMode ? "brain_learning_lab" : "independent_learning_queue",
    pipelineStage: learningMode ? "learning" : "deferred_learning",
    observedPipelineStage: "unknown",
    learningDisposition: learningMode ? "propose_new_or_evolved_core_type" : "queue_for_independent_learning",
    capabilityStrategy: "unknown",
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

function readJsonFile(filename, fallback) {
  try {
    return JSON.parse(fs.readFileSync(filename, "utf8"));
  } catch (_error) {
    return fallback;
  }
}

function buildRuntimeCompatibility(matrixValue) {
  const matrix = asRecord(matrixValue);
  const universe = new Set(stringArray(matrix.capability_universe));
  const clientEntries = Object.entries(asRecord(matrix.clients)).filter(([, row]) => isRecord(row));
  if (!universe.size || !clientEntries.length) {
    throw new Error("nuvio_runtime_compatibility_matrix_missing");
  }
  const supportedSets = clientEntries.map(([, row]) => new Set(stringArray(row.brain_capabilities)));
  const supportedCapabilities = [...universe].filter((capability) => supportedSets.every((set) => set.has(capability))).sort();
  const supported = new Set(supportedCapabilities);
  const clients = {};
  for (const [clientId, row] of clientEntries) {
    const supportedRange = asRecord(row.supported_version_code);
    const baseline = asRecord(row.baseline);
    const current = asRecord(row.current_audited);
    clients[clientId] = {
      family: stringValue(row.family),
      baselineVersion: stringValue(baseline.version_name),
      baselineVersionCode: finiteNumber(baseline.version_code, 0),
      currentVersion: stringValue(current.version_name),
      currentVersionCode: finiteNumber(current.version_code, 0),
      supportedMinVersionCode: finiteNumber(supportedRange.min, 0),
      supportedMaxVersionCode: finiteNumber(supportedRange.max, 0),
    };
  }
  return {
    matrixVersion: finiteNumber(matrix.schema_version, 1),
    supportedCapabilities,
    invalidCapabilities: [...universe].filter((capability) => !supported.has(capability)).sort(),
    clients,
  };
}

function normalizeLearnedSkills(value) {
  if (Array.isArray(value)) return value.filter(isRecord);
  if (isRecord(value)) return Object.values(value).filter(isRecord);
  return [];
}

function resolveRepairTarget(failureClass, capabilityStrategy, observedPipelineStage, mode) {
  const table = asRecord(coreRepairConfig.failureClasses);
  const row = asRecord(table[stringValue(failureClass, "unknown_failure")]);
  const configuredScope = stringValue(row.scope, "learning");
  const learningMode = stringValue(mode, "quick") === "learning";
  if (configuredScope === "learning" && !learningMode) {
    return {
      scope: "deferred",
      repairType: stringValue(row.repairType, "architecture_gap"),
      engine: "independent_learning_queue",
      pipelineStage: "deferred_learning",
      profiles: [],
      capabilityStrategy: stringValue(capabilityStrategy, "unknown"),
      learningDisposition: "queue_for_independent_learning",
      observedPipelineStage: stringValue(observedPipelineStage, "unknown"),
    };
  }
  return {
    scope: configuredScope,
    repairType: stringValue(row.repairType, "architecture_gap"),
    engine: stringValue(row.engine, "brain_learning_lab"),
    pipelineStage: stringValue(row.pipelineStage, "learning"),
    profiles: stringArray(row.profiles),
    capabilityStrategy: stringValue(capabilityStrategy, "unknown"),
    learningDisposition: configuredScope === "learning"
      ? "propose_new_or_evolved_core_type"
      : configuredScope === "none"
        ? "none"
        : learningMode
          ? "observe_core_type_then_explore_if_unresolved"
          : "core_repair_only",
    observedPipelineStage: stringValue(observedPipelineStage, "unknown"),
  };
}

function profilesForRepairTarget(plan, repairTarget) {
  if (stringValue(plan.action) !== "probe-targeted-repair") return [];
  if (repairTarget.scope !== "capability") return [];
  return [...new Set(stringArray(repairTarget.profiles))];
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
  const providerObservations = observations.filter((row) => row.infrastructure !== true);
  const providerStatuses = providerObservations.map((row) => Number(row.status)).filter(Number.isFinite);
  const blocked = providerStatuses.find((code) => [401, 403, 407, 429, 451].includes(code));
  const gone = providerStatuses.find((code) => [404, 410].includes(code));
  const terminalMediaFailures = providerObservations.filter((row) => {
    const code = Number(row.status);
    return ([401, 403, 407, 429, 451, 404, 410].includes(code) && isTerminalMediaObservation(row));
  });
  const terminalMediaStatuses = terminalMediaFailures.map((row) => Number(row.status)).filter(Number.isFinite);
  const providerSuccessObserved = providerObservations.some((row) => {
    const code = Number(row.status);
    return code >= 200 && code < 300 && !isTerminalMediaObservation(row);
  });
  const fixture = asRecord(tests[0]?.fixture);
  const observedPipelineStage = highestObservedPipelineStage(observations, tests, returned, playable);
  const metadata = asRecord(candidate.metadata);
  const supportedTypes = stringArray(metadata.supportedTypes);
  const mediaType = stringValue(fixture.category ?? fixture.mediaType ?? supportedTypes[0], "movie").toLowerCase();
  const identityContradiction = finiteNumber(evidence.identity_contradiction_count, 0) > 0 || finiteNumber(evidence.duration_identity_mismatch_count, 0) > 0 || /identity|duration.*mismatch/.test(failureText);
  const invoked = !/not[_ -]?invoked|invalid[_ -]?request[_ -]?argument|object%20object|object object/.test(failureText);
  const structuredParseFailure = status === "runtime_error" && playable === 0 && /(?:json(?:\.parse)?|syntaxerror|structured)[^\n]{0,120}(?:unexpected|invalid|escape|unterminated|control character|parse)|(?:unexpected token|bad escape|invalid json)/.test(failureText);
  const contractDrift = status === "runtime_error" && /invalid[_ -]?request[_ -]?argument|object%20object|object object|signature|argument/.test(failureText);
  const audioTrackGap = /(?:missing|no|without)[_ -]?(?:usable[_ -]?)?audio|audio[_ -]?(?:track|stream)[_ -]?(?:missing|absent|gap)|silent[_ -]?media/.test(failureText);

  if (audioTrackGap) return { invoked, audioTrackGap: true, request: { mediaType }, observedPipelineStage };
  if (playable > 0 && !identityContradiction) {
    return { invoked, contractDrift, playableStreams: playable, request: { mediaType }, observedPipelineStage, stages: { validation: { attempted: true, playable: true, playableCount: playable, statuses } } };
  }
  if (identityContradiction) return { invoked, suspicious: true, request: { mediaType }, observedPipelineStage };
  if (structuredParseFailure) return { invoked, structuredParseFailure: true, request: { mediaType }, observedPipelineStage };
  if (status === "provider_unreachable" && /dns|enotfound|eai_again|getaddrinfo/.test(failureText)) {
    return { invoked, dns: { ok: false }, request: { mediaType }, observedPipelineStage };
  }
  if (returned > 0) {
    return {
      invoked, contractDrift, request: { mediaType }, observedPipelineStage, playableStreams: 0,
      stages: {
        player: { attempted: true, found: true },
        media: { attempted: true, found: true, streamCount: returned },
        validation: { attempted: true, observed: true, playable: false, playableCount: 0, statuses: statuses.length ? statuses : [gone || blocked || 200] },
      },
    };
  }
  if (terminalMediaStatuses.length && providerSuccessObserved) {
    return {
      invoked, contractDrift, request: { mediaType }, observedPipelineStage, playableStreams: 0,
      stages: {
        player: { attempted: true, found: true },
        media: { attempted: true, found: true, streamCount: 0 },
        validation: { attempted: true, observed: true, playable: false, playableCount: 0, statuses: terminalMediaStatuses },
      },
    };
  }
  if (status === "blocked" || blocked) {
    return { invoked, dns: { ok: true }, request: { mediaType }, observedPipelineStage, stages: { homepage: { status: blocked || 403 } } };
  }
  if (/episode/.test(failureText)) {
    return { invoked, request: { mediaType: mediaType === "movie" ? "tv" : mediaType }, observedPipelineStage, stages: { search: { attempted: true, status: 200, matches: 1 }, identity: { attempted: true, matched: true }, detail: { attempted: true, found: true }, episode: { attempted: true, found: false } } };
  }
  if (/player|iframe|embed/.test(failureText) && pipelineStageRank(observedPipelineStage) < pipelineStageRank("player")) {
    return { invoked, request: { mediaType }, observedPipelineStage, stages: { player: { attempted: true, found: false } } };
  }
  if (pipelineStageRank(observedPipelineStage) >= pipelineStageRank("player") && returned === 0) {
    return { invoked, request: { mediaType }, observedPipelineStage, stages: { player: { attempted: true, found: true }, media: { attempted: true, found: false } } };
  }
  if (/media|stream|hls|dash|m3u8|mp4/.test(failureText) && !/no[_ -]?streams?/.test(failureText)) {
    return { invoked, request: { mediaType }, observedPipelineStage, stages: { player: { attempted: true, found: true }, media: { attempted: true, found: false } } };
  }
  if (gone || /provider_http_error|404|410|no[_ -]?streams?|runtime_empty/.test(failureText) || ["no_streams", "reachable", "degraded", "unavailable", "provider_unreachable"].includes(status)) {
    return { invoked, request: { mediaType }, observedPipelineStage, stages: { search: { attempted: true, status: gone || 200, matches: 0 } } };
  }
  return { invoked, contractDrift, request: { mediaType }, observedPipelineStage, playableStreams: 0 };
}

function pipelineStageRank(stage) {
  const order = ["unknown", "source", "provider", "search", "detail", "episode", "player", "media", "reader"];
  const index = order.indexOf(stringValue(stage, "unknown"));
  return index >= 0 ? index : 0;
}

function highestObservedPipelineStage(observations, tests, returned, playable) {
  let stage = "provider";
  const bump = (candidate) => {
    if (pipelineStageRank(candidate) > pipelineStageRank(stage)) stage = candidate;
  };
  for (const row of observations) {
    const value = stringValue(row.stage).toLowerCase();
    if (/^(?:origin_probe|homepage|dns)$/.test(value)) bump("source");
    else if (/^(?:search|catalogue)$/.test(value)) bump("search");
    else if (/^(?:content_lookup|detail)$/.test(value)) bump("detail");
    else if (/^(?:episode|season)$/.test(value)) bump("episode");
    else if (/^(?:player|embed)$/.test(value)) bump("player");
    else if (/^(?:media|stream|hls|dash)$/.test(value)) bump("media");
    else if (/^(?:reader|playback|validation)$/.test(value)) bump("reader");
  }
  for (const row of tests) {
    const failure = stringValue(row.failure_class).toLowerCase();
    if (/reader|playback|decoder|audio|duration/.test(failure)) bump("reader");
    else if (/media|stream|hls|dash/.test(failure) && !/no[_ -]?streams?/.test(failure)) bump("media");
    else if (/player|iframe|embed/.test(failure)) bump("player");
    else if (/episode|season/.test(failure)) bump("episode");
  }
  if (finiteNumber(returned, 0) > 0) bump("media");
  if (finiteNumber(playable, 0) > 0) bump("reader");
  return stage;
}

function isTerminalMediaObservation(row) {
  const stage = stringValue(row.stage).toLowerCase();
  if (/^(?:media|stream|playback|validation|hls|dash)$/.test(stage)) return true;
  const locator = [row.url, row.path, row.path_pattern, row.pathPattern]
    .map((value) => stringValue(value))
    .join(" ")
    .toLowerCase();
  return /\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?&#\s]|$)/.test(locator) || /\/(?:hls|hls2)\//.test(locator);
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
