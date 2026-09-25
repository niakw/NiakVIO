#!/usr/bin/env node
import fs from "node:fs";
import crypto from "node:crypto";
import process from "node:process";
import { BRAIN_CONTROL_PLANE_VERSION, classifyFailure, planRepair } from "../src/repair-brain.mjs";
import { evidenceSignature } from "../src/recipe-memory.mjs";

let input;
let rawInput = "";
try {
  const inputFile = String(process.env.NUVIO_BRAIN_PLANNER_INPUT_FILE || "").trim();
  rawInput = inputFile ? fs.readFileSync(inputFile, "utf8") : fs.readFileSync(0, "utf8");
  input = JSON.parse(rawInput || "{}");
} catch (error) {
  const reason = String(error?.name || "Error").replace(/[^A-Za-z0-9_.-]/g, "").slice(0, 48);
  process.stderr.write(`brain_planner_input_invalid bytes=${Buffer.byteLength(rawInput || "", "utf8")} reason=${reason}\n`);
  process.exit(2);
}

const policy = asRecord(input.policy);
const production = asRecord(policy.production);
const maturity = asRecord(policy.skillMaturity);
const globalSkillConfig = readJsonFile("engine_v2/config/global-repair-skills.json", {});
const coreRepairConfig = readJsonFile("engine_v2/config/core-repair-types.json", {});
const providerOverrides = readJsonFile("provider-overrides.json", {});
const learningMode = stringValue(input.mode, "quick") === "learning";
const skillTransfer = asRecord(production.learnedSkillTransferPolicy);
const learnedSkillInputAllowed = learningMode || production.learnedSkillInputAllowed === true;
const negativeMemoryPolicy = asRecord(production.negativeExperimentMemory);
const negativeMemory = asArray(input.negativeMemory).filter(isRecord);
const historicalSolutions = asArray(input.historicalSolutions).filter(isRecord);
const llmGuidance = asArray(input.llmGuidance).filter(isRecord);
const inputLearnedSkills = normalizeLearnedSkills(input.learnedSkills);
const learnedSkills = [
  ...(
    learnedSkillInputAllowed
      ? inputLearnedSkills
      : inputLearnedSkills.filter((skill) => (
          skill.validated === true
          && skill.sameProviderPositiveProgram === true
        ))
  ),
  ...(learningMode ? normalizeLearnedSkills(asRecord(globalSkillConfig).skills) : []),
];
const runtimeCompatibility = buildRuntimeCompatibility(
  readJsonFile("automation/nuvio-client-compatibility-matrix.json", {}),
);
const HISTORICAL_SOLUTION_PROFILES = {
  provider_owned_origin_header_and_domain_replay: "provider_origin_failover_v1",
  search_detail_player_terminal_traversal: "proven_route_terminal_traversal_v1",
  terminal_media_extractor_with_playback_validation: "chain_terminal_extractor_v1",
  same_provider_candidate_program_replay: "retained_candidate_replay_v1",
  proven_request_program_and_terminal_extraction: "player_media_extractor_v1",
};
const LLM_ADVISOR_PROFILES = new Set([
  "provider_origin_failover_v1",
  "proven_route_terminal_traversal_v1",
  "chain_terminal_extractor_v1",
  "retained_candidate_replay_v1",
  "player_media_extractor_v1",
  "search_contract_inference_v1",
]);
const POST_EXHAUSTION_STRATEGIES = {
  provider_transport_gap: [
    { profile: "transport_request_differential_v1", method: "provider-owned-request-differential" },
    { profile: "provider_session_bootstrap_replay_v1", method: "provider-owned-session-bootstrap-replay" },
    { profile: "runtime_response_salvage_v1", method: "successful-runtime-response-salvage" },
  ],
  transport_blocked: [
    { profile: "transport_request_differential_v1", method: "provider-owned-request-differential" },
    { profile: "provider_session_bootstrap_replay_v1", method: "provider-owned-session-bootstrap-replay" },
    { profile: "runtime_response_salvage_v1", method: "successful-runtime-response-salvage" },
  ],
  route_proven_gap: [
    { profile: "route_transition_graph_v1", method: "provider-owned-route-transition-graph" },
    { profile: "route_peer_transition_replay_v1", method: "structural-peer-route-transition-replay" },
    { profile: "identity_alias_search_traversal_v1", method: "tmdb-identity-alias-search-traversal" },
    { profile: "runtime_response_salvage_v1", method: "successful-runtime-response-salvage" },
    { profile: "document_request_contract_mining_v1", method: "provider-document-request-contract-mining" },
  ],
  chain_terminal_gap: [
    { profile: "terminal_transition_graph_v1", method: "terminal-response-transition-graph" },
    { profile: "terminal_request_program_inference_v1", method: "terminal-request-program-inference" },
    { profile: "runtime_response_salvage_v1", method: "successful-runtime-response-salvage" },
    { profile: "document_request_contract_mining_v1", method: "provider-document-request-contract-mining" },
  ],
  candidate_replay_gap: [
    { profile: "candidate_divergence_trace_v1", method: "retained-candidate-divergence-trace" },
    { profile: "candidate_request_program_replay_v1", method: "retained-request-program-replay" },
    { profile: "runtime_response_salvage_v1", method: "successful-runtime-response-salvage" },
    { profile: "identity_alias_search_traversal_v1", method: "tmdb-identity-alias-search-traversal" },
    { profile: "document_request_contract_mining_v1", method: "provider-document-request-contract-mining" },
  ],
  media_extraction_gap: [
    { profile: "player_protocol_family_replay_v1", method: "player-protocol-family-replay" },
    { profile: "media_response_shape_inference_v1", method: "media-response-shape-inference" },
    { profile: "runtime_response_salvage_v1", method: "successful-runtime-response-salvage" },
    { profile: "document_request_contract_mining_v1", method: "provider-document-request-contract-mining" },
  ],
  search_gap: [
    { profile: "search_contract_inference_v1", method: "search-contract-inference" },
    { profile: "search_response_route_binding_v1", method: "search-response-route-binding" },
    { profile: "identity_alias_search_traversal_v1", method: "tmdb-identity-alias-search-traversal" },
    { profile: "runtime_response_salvage_v1", method: "successful-runtime-response-salvage" },
    { profile: "document_request_contract_mining_v1", method: "provider-document-request-contract-mining" },
  ],
};

const EVOLVED_STRATEGY_IMPLEMENTATION_FILES = [
  "scripts/adaptive_runtime/runtime_repair.py",
  "scripts/adaptive_runtime/runtime_recovery_generator.py",
  "scripts/provider_patches/adaptive_runtime_recovery_v5.py",
];

function strategyImplementationFingerprint(profile) {
  const normalized = stringValue(profile).toLowerCase();
  if (!normalized || normalized === "provider_positive_program_replay_v1") return "";
  const hash = crypto.createHash("sha256");
  hash.update(`profile:${normalized}\n`);
  for (const file of EVOLVED_STRATEGY_IMPLEMENTATION_FILES) {
    try {
      hash.update(`file:${file}\n`);
      hash.update(fs.readFileSync(file));
    } catch (_error) {
      return "";
    }
  }
  return hash.digest("hex");
}

const LLM_FAILURE_FAMILIES = Object.freeze({
  route_proven_gap: "route-terminal",
  provider_transport_gap: "route-terminal",
  transport_blocked: "route-terminal",
  search_gap: "route-terminal",
  chain_terminal_gap: "terminal-media",
  media_extraction_gap: "terminal-media",
  playback_context_gap: "terminal-media",
});

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

function causalStrategyProfile(failureClass, variant, generation, finalVariant) {
  if (finiteNumber(variant, -1) !== finiteNumber(finalVariant, -2)) return "";
  const base = {
    provider_transport_gap: "provider_origin_failover_v1",
    route_proven_gap: "proven_route_terminal_traversal_v1",
    chain_terminal_gap: "chain_terminal_extractor_v1",
    candidate_replay_gap: "retained_candidate_replay_v1",
    media_extraction_gap: "player_media_extractor_v1",
  }[stringValue(failureClass).toLowerCase()];
  if (!base) return "";
  const currentGeneration = Math.max(1, finiteNumber(generation, 1));
  return currentGeneration <= 2 ? base : `${base}_g${currentGeneration}`;
}

function generationProfile(base, generation) {
  if (!base) return "";
  const currentGeneration = Math.max(1, finiteNumber(generation, 1));
  return currentGeneration <= 2 ? base : `${base}_g${currentGeneration}`;
}

function historicalStrategyHint(providerId, failureClass, generation, memoryRows, rotateEvery) {
  const provider = stringValue(providerId).toLowerCase();
  const failure = stringValue(failureClass).toLowerCase();
  const candidates = historicalSolutions
    .filter((row) => {
      if (stringValue(row.failureClass).toLowerCase() !== failure) return false;
      const providers = stringArray(row.providers).map((value) => value.toLowerCase());
      return providers.length === 0 || providers.includes("global") || providers.includes(provider);
    })
    .map((row) => ({
      caseId: stringValue(row.id),
      solutionClass: stringValue(row.solutionClass).toLowerCase(),
      providerSpecific: stringArray(row.providers).map((value) => value.toLowerCase()).includes(provider),
    }))
    .filter((row) => Boolean(HISTORICAL_SOLUTION_PROFILES[row.solutionClass]))
    .sort((a, b) => Number(b.providerSpecific) - Number(a.providerSpecific) || a.caseId.localeCompare(b.caseId));
  for (const row of candidates) {
    const profile = generationProfile(HISTORICAL_SOLUTION_PROFILES[row.solutionClass], generation);
    const alreadyFailed = memoryRows.some((memory) => (
      stringValue(memory.profile) === profile
      && Math.max(0, finiteNumber(memory.consecutiveFailures, 0)) >= rotateEvery
    ));
    if (!alreadyFailed) return { profile, caseId: row.caseId, solutionClass: row.solutionClass };
  }
  return { profile: "", caseId: "", solutionClass: "" };
}

function postExhaustionStrategyHint(failureClass, memoryRows, rotateEvery) {
  const failure = stringValue(failureClass).toLowerCase();
  const candidates = POST_EXHAUSTION_STRATEGIES[failure] ?? [];
  for (let index = 0; index < candidates.length; index += 1) {
    const row = candidates[index];
    const implementationFingerprint = strategyImplementationFingerprint(row.profile);
    const alreadyFailed = memoryRows.some((memory) => {
      if (
        stringValue(memory.profile) !== row.profile
        || Math.max(0, finiteNumber(memory.consecutiveFailures, 0)) < rotateEvery
      ) return false;
      const rememberedFingerprint = stringValue(memory.strategyImplementationFingerprint).toLowerCase();
      return implementationFingerprint
        ? rememberedFingerprint === implementationFingerprint
        : true;
    });
    if (!alreadyFailed) {
      return {
        profile: row.profile,
        method: row.method,
        index,
        strategyImplementationFingerprint: implementationFingerprint,
      };
    }
  }
  return { profile: "", method: "", index: -1, strategyImplementationFingerprint: "" };
}

function canonicalFailureClass(value) {
  return stringValue(value).toLowerCase().replaceAll("-", "_");
}

function llmFailureCompatibility(guidanceFailure, currentFailure) {
  const source = canonicalFailureClass(guidanceFailure);
  const current = canonicalFailureClass(currentFailure);
  if (!source) return "unspecified";
  if (source === current) return "exact";
  const sourceFamily = LLM_FAILURE_FAMILIES[source] ?? "";
  const currentFamily = LLM_FAILURE_FAMILIES[current] ?? "";
  return sourceFamily && sourceFamily === currentFamily ? "family" : "";
}

function llmAdvisorStrategyHint(providerId, failureClass, memoryRows, rotateEvery) {
  const provider = stringValue(providerId).toLowerCase();
  const failure = canonicalFailureClass(failureClass);
  const rows = llmGuidance
    .map((row) => ({
      ...row,
      failureCompatibility: llmFailureCompatibility(row.failureClass, failure),
    }))
    .filter((row) => {
      const confidence = finiteNumber(row.confidence, 0);
      return (
        stringValue(row.providerId).toLowerCase() === provider
        && stringValue(row.targetLayer).toLowerCase() === "provider"
        && row.priorOnly === true
        && confidence >= 0.80
        && LLM_ADVISOR_PROFILES.has(stringValue(row.profile).toLowerCase())
        && Boolean(row.failureCompatibility)
        && (row.failureCompatibility !== "family" || confidence >= 0.90)
      );
    })
    .sort((a, b) => (
      Number(b.failureCompatibility === "exact") - Number(a.failureCompatibility === "exact")
      || finiteNumber(b.confidence, 0) - finiteNumber(a.confidence, 0)
    ));
  for (const row of rows) {
    const profile = stringValue(row.profile).toLowerCase();
    const fingerprintRaw = stringValue(row.experimentFingerprint).toLowerCase();
    const experimentFingerprint = /^[0-9a-f]{64}$/.test(fingerprintRaw) ? fingerprintRaw : "";
    const alreadyFailed = memoryRows.some((memory) => {
      if (
        stringValue(memory.profile).toLowerCase() !== profile
        || Math.max(0, finiteNumber(memory.consecutiveFailures, 0)) < rotateEvery
      ) return false;
      const remembered = stringValue(memory.llmAdvisorExperimentFingerprint).toLowerCase();
      return experimentFingerprint ? remembered === experimentFingerprint : !remembered;
    });
    if (alreadyFailed) continue;
    return {
      profile,
      strategy: stringValue(row.strategy).toLowerCase(),
      confidence: finiteNumber(row.confidence, 0),
      sourceFailureClass: canonicalFailureClass(row.failureClass),
      failureCompatibility: row.failureCompatibility,
      experiment: asRecord(row.experiment),
      experimentFingerprint,
    };
  }
  return {
    profile: "",
    strategy: "",
    confidence: 0,
    sourceFailureClass: "",
    failureCompatibility: "",
    experiment: {},
    experimentFingerprint: "",
  };
}

function providerPositiveProgramReplayHint(reusableSkills, memoryRows, rotateEvery) {
  const profile = "provider_positive_program_replay_v1";
  const strictPrograms = reusableSkills.filter(
    (skill) => skill.sameProviderPositiveProgram === true,
  );
  if (!strictPrograms.length) {
    return { profile: "", method: "", index: -1, positiveProgramFingerprint: "" };
  }
  const fingerprints = [...new Set(
    strictPrograms
      .map((skill) => stringValue(skill.positiveProgramFingerprint).toLowerCase())
      .filter((value) => /^[0-9a-f]{64}$/.test(value)),
  )].sort();
  // Every same-provider positive skill is projected from the same durable
  // provider program set, so one aggregate fingerprint is expected. Keep a
  // deterministic aggregate if older mixed skill state temporarily exposes
  // more than one value rather than falling back to profile-wide suppression.
  const positiveProgramFingerprint = fingerprints.length === 1
    ? fingerprints[0]
    : fingerprints.length > 1
      ? fingerprints.join(":")
      : "";
  const alreadyFailed = memoryRows.some((memory) => (
    stringValue(memory.profile) === profile
    && Math.max(0, finiteNumber(memory.consecutiveFailures, 0)) >= rotateEvery
    && (
      !positiveProgramFingerprint
      || stringValue(memory.positiveProgramFingerprint).toLowerCase() === positiveProgramFingerprint
    )
  ));
  if (alreadyFailed) {
    return { profile: "", method: "", index: -1, positiveProgramFingerprint };
  }
  return {
    profile,
    method: "strict-same-provider-positive-program-replay",
    index: -1,
    positiveProgramFingerprint,
  };
}

function buildPlan(item) {
  const candidate = asRecord(item.candidate);
  const result = asRecord(item.result);
  const state = asRecord(item.state);
  const evidence = applyCensusPrior(deriveEvidence(candidate, result), candidate);
  evidence.failureClass = classifyFailure(evidence);
  const signature = evidenceSignature(evidence);
  const providerId = stringValue(candidate.canonical_id ?? candidate.upstream_id).toLowerCase();
  const capabilityStrategy = stringValue(asRecord(asRecord(providerOverrides.provider_capabilities)[providerId]).strategy, "unknown").toLowerCase();
  const rotateEvery = Math.max(1, finiteNumber(negativeMemoryPolicy.rotateExperimentAfterFailures, 1));
  const maxVariants = Math.max(1, finiteNumber(negativeMemoryPolicy.maxVariantsPerSignature, 5));
  const finalVariant = maxVariants - 1;
  const finalVariantGeneration = Math.max(1, finiteNumber(negativeMemoryPolicy.finalVariantGeneration, 1));
  const maxLearningGenerations = Math.max(
    finalVariantGeneration,
    finiteNumber(negativeMemoryPolicy.maxLearningGenerationsPerSignature, finalVariantGeneration),
  );
  const allMemoryMatches = negativeMemory.filter((row) => {
    if (stringValue(row.providerId).toLowerCase() !== providerId) return false;
    const failure = stringValue(row.failureClass);
    if (failure && failure !== evidence.failureClass) return false;
    const rowSignature = stringValue(row.signature);
    if (rowSignature && rowSignature !== signature) return false;
    // Historical success must not grant permanent immunity to a strategy that
    // is failing on current bytes. Accepted experiments reset
    // consecutiveFailures to zero; later bounded failures raise it again.
    // Legacy rows without that counter remain negative only when they never
    // recorded a success.
    const consecutiveFailures = Math.max(0, finiteNumber(row.consecutiveFailures, 0));
    const failures = Math.max(0, finiteNumber(row.failures, 0));
    const successes = Math.max(0, finiteNumber(row.successes, 0));
    return consecutiveFailures > 0 || (successes === 0 && failures > 0);
  });
  const finalProductionProfile = causalStrategyProfile(
    evidence.failureClass,
    finalVariant,
    finalVariantGeneration,
    finalVariant,
  );
  const productionMemoryMatches = allMemoryMatches.filter((row) => {
    const variant = Math.max(0, Math.min(finalVariant, finiteNumber(row.experimentVariant, 0)));
    if (variant !== finalVariant) return true;
    const generation = Math.max(1, finiteNumber(row.experimentGeneration, 1));
    if (generation !== finalVariantGeneration) return false;
    // Final causal strategies have their own memory identity. Historical
    // failures recorded under the generic adaptive profile must not pre-exhaust
    // a named strategy that has never actually run.
    if (finalProductionProfile) {
      return stringValue(row.profile) === finalProductionProfile;
    }
    return true;
  });
  const baseVariantStats = new Map();
  for (const row of allMemoryMatches) {
    const variant = Math.max(0, Math.min(finalVariant, finiteNumber(row.experimentVariant, 0)));
    if (variant === finalVariant) continue;
    const current = baseVariantStats.get(variant) ?? { failures: 0, consecutiveFailures: 0 };
    current.failures += Math.max(0, finiteNumber(row.failures, 0));
    current.consecutiveFailures = Math.max(current.consecutiveFailures, Math.max(0, finiteNumber(row.consecutiveFailures, 0)));
    baseVariantStats.set(variant, current);
  }
  let experimentVariant = 0;
  let experimentGeneration = 1;
  let experimentExhausted = false;
  if (learningMode) {
    const baseExhausted = Array.from({ length: finalVariant }, (_unused, variant) => variant)
      .every((variant) => {
        const stats = baseVariantStats.get(variant);
        return stats && stats.consecutiveFailures >= rotateEvery;
      });
    if (!baseExhausted) {
      for (let variant = 0; variant < finalVariant; variant += 1) {
        const stats = baseVariantStats.get(variant);
        if (!stats || stats.consecutiveFailures < rotateEvery) {
          experimentVariant = variant;
          break;
        }
      }
    } else {
      experimentVariant = finalVariant;
      const failedGenerations = new Set();
      for (const row of allMemoryMatches) {
        const variant = Math.max(0, Math.min(finalVariant, finiteNumber(row.experimentVariant, 0)));
        if (variant !== finalVariant) continue;
        const generation = Math.max(1, finiteNumber(row.experimentGeneration, 1));
        if (generation < finalVariantGeneration || generation > maxLearningGenerations) continue;
        const expectedProfile = causalStrategyProfile(
          evidence.failureClass,
          finalVariant,
          generation,
          finalVariant,
        );
        if (expectedProfile && stringValue(row.profile) !== expectedProfile) continue;
        if (Math.max(0, finiteNumber(row.consecutiveFailures, 0)) >= rotateEvery) {
          failedGenerations.add(generation);
        }
      }
      experimentGeneration = finalVariantGeneration;
      while (
        experimentGeneration <= maxLearningGenerations
        && failedGenerations.has(experimentGeneration)
      ) {
        experimentGeneration += 1;
      }
      if (experimentGeneration > maxLearningGenerations) {
        experimentGeneration = maxLearningGenerations;
        experimentExhausted = true;
      }
    }
  } else {
    const variantStats = new Map();
    for (const row of productionMemoryMatches) {
      const variant = Math.max(0, Math.min(finalVariant, finiteNumber(row.experimentVariant, 0)));
      const current = variantStats.get(variant) ?? { failures: 0, consecutiveFailures: 0 };
      current.failures += Math.max(0, finiteNumber(row.failures, 0));
      current.consecutiveFailures = Math.max(current.consecutiveFailures, Math.max(0, finiteNumber(row.consecutiveFailures, 0)));
      variantStats.set(variant, current);
    }
    experimentExhausted = Array.from({ length: maxVariants }, (_unused, variant) => variant)
      .every((variant) => {
        const stats = variantStats.get(variant);
        return stats && stats.consecutiveFailures >= rotateEvery;
      });
    if (!experimentExhausted) {
      for (let variant = 0; variant < maxVariants; variant += 1) {
        const stats = variantStats.get(variant);
        if (!stats || stats.consecutiveFailures < rotateEvery) {
          experimentVariant = variant;
          break;
        }
      }
    } else {
      experimentVariant = finalVariant;
    }
    experimentGeneration = experimentVariant === finalVariant ? finalVariantGeneration : 1;
  }
  const negativeMemoryMatches = allMemoryMatches.reduce((sum, row) => sum + Math.max(1, finiteNumber(row.failures, 0)), 0);
  const reusable = learnedSkills
    .filter((skill) => {
      const providers = stringArray(skill.providers ?? skill.provenOnProviders).map((value) => value.toLowerCase());
      const sameProviderPositiveProgram = skill.sameProviderPositiveProgram === true && providers.includes(providerId);
      // Strict same-provider positive programs are allowed to survive diagnostic
      // label drift. They remain priors only: the generated candidate still has
      // to pass current-byte playback, identity and non-regression gates.
      return sameProviderPositiveProgram
        || !skill.failureClass
        || skill.failureClass === evidence.failureClass
        || skill.failure_class === evidence.failureClass;
    })
    .map((skill) => {
      const providers = stringArray(skill.providers ?? skill.provenOnProviders).map((value) => value.toLowerCase());
      const sameProviderPositiveProgram = skill.sameProviderPositiveProgram === true && providers.includes(providerId);
      const signatures = stringArray(skill.signatures ?? skill.evidenceSignatures);
      const strategies = stringArray(skill.capabilityStrategies ?? skill.capabilityStrategy).map((value) => value.toLowerCase());
      const stages = stringArray(skill.observedPipelineStages ?? skill.observedPipelineStage).map((value) => value.toLowerCase());
      const confidence = finiteNumber(skill.confidence, 0);
      const successCount = finiteNumber(skill.successCount, 0);
      const failureCount = finiteNumber(skill.failureCount, 0);
      const transferScore = learnedSkillTransferScore({
        skill,
        providerId,
        signature,
        capabilityStrategy,
        observedPipelineStage: stringValue(evidence.observedPipelineStage, "unknown"),
        providers,
        signatures,
        strategies,
        stages,
        confidence,
        successCount,
        failureCount,
        sameProviderPositiveProgram,
      });
      return {
        id: stringValue(skill.id),
        // planRepair performs a second failure-class filter. A strictly
        // validated same-provider program is intentionally failure-agnostic at
        // this point so it can be replayed after a diagnostic relabel.
        failureClass: sameProviderPositiveProgram ? null : (skill.failureClass ?? skill.failure_class ?? null),
        originalFailureClass: skill.failureClass ?? skill.failure_class ?? null,
        capabilities: stringArray(skill.capabilities),
        clientVersions: asRecord(skill.clientVersions ?? skill.runtimeVersions),
        actions: stringArray(skill.actions).length ? stringArray(skill.actions) : [`apply learned profile ${stringValue(skill.profile)}`],
        profile: stringValue(skill.profile) || null,
        learned: true,
        maturity: stringValue(skill.maturity, "experimental"),
        confidence,
        successCount,
        failureCount,
        providers,
        signatures,
        capabilityStrategies: strategies,
        observedPipelineStages: stages,
        transferScore,
        validated: skill.validated === true,
        sameProviderPositiveProgram,
        positiveProgramFingerprint: sameProviderPositiveProgram
          ? stringValue(asRecord(skill.positiveProgramFingerprintsByProvider)[providerId]).toLowerCase()
          : "",
        source: stringValue(skill.source),
      };
    })
    .filter((skill) => skill.id && skill.profile)
    .filter((skill) => (
      learningMode
      || skill.sameProviderPositiveProgram === true
      || learnedSkillTransferEligible(skill)
    ))
    .sort((a, b) => b.transferScore - a.transferScore || b.confidence - a.confidence || b.successCount - a.successCount || a.id.localeCompare(b.id));

  const signatureCounts = asRecord(state.signatureCounts);
  const repeatedSignatureCount = finiteNumber(
    signatureCounts[signature],
    finiteNumber(state.repeatedSignatureCount, 0),
  );
  const explorationBudget = input.explorationChain === true
    ? asRecord(production.explorationChainBudget)
    : {};
  const plan = planRepair(evidence, {
    signature,
    learnedSkills: reusable,
    runtimeCompatibility,
    maxHypotheses: finiteNumber(production.maxHypotheses, 3),
    budget: {
      maxHypotheses: finiteNumber(production.maxHypotheses, 3),
      maxMutations: finiteNumber(explorationBudget.maxMutationsPerProvider, finiteNumber(production.maxMutationsPerProvider, 2)),
      maxRepeatedSignature: finiteNumber(explorationBudget.maxRepeatedSignature, finiteNumber(production.maxRepeatedSignature, 2)),
      maxGeneratedBytes: finiteNumber(explorationBudget.maxGeneratedBytesPerProvider, finiteNumber(production.maxGeneratedBytesPerProvider, 180000)),
      maxElapsedMs: finiteNumber(explorationBudget.maxElapsedMsPerProvider, finiteNumber(production.maxElapsedMsPerProvider, 45000)),
      mutationCount: finiteNumber(state.mutationCount, 0),
      repeatedSignatureCount,
      generatedBytes: finiteNumber(state.generatedBytes, 0),
      elapsedMs: finiteNumber(state.elapsedMs, 0),
    },
    learningLab: stringValue(input.mode) === "learning",
    coreMutationRequested: state.coreMutationRequested === true,
  });
  const hypotheses = asArray(plan.hypotheses).filter(isRecord);
  const baseRepairTarget = resolveRepairTarget(plan.failureClass, capabilityStrategy, evidence.observedPipelineStage, stringValue(input.mode, "quick"));
  const positiveProgramReplayHint = experimentExhausted
    ? providerPositiveProgramReplayHint(reusable, allMemoryMatches, rotateEvery)
    : { profile: "", method: "", index: -1, positiveProgramFingerprint: "" };
  const postExhaustionHint = positiveProgramReplayHint.profile
    ? positiveProgramReplayHint
    : (learningMode && experimentExhausted)
      ? postExhaustionStrategyHint(evidence.failureClass, allMemoryMatches, rotateEvery)
      : { profile: "", method: "", index: -1 };
  const strategyEscalated = Boolean(postExhaustionHint.profile);
  const providerPositiveProgramProductionRescue = (
    !learningMode
    && experimentExhausted
    && postExhaustionHint.profile === "provider_positive_program_replay_v1"
    && /^[0-9a-f]{64}$/.test(stringValue(postExhaustionHint.positiveProgramFingerprint).toLowerCase())
  );
  const repairTarget = experimentExhausted
    ? (
        strategyEscalated
          ? (
              providerPositiveProgramProductionRescue
                ? {
                    ...baseRepairTarget,
                    profiles: [postExhaustionHint.profile],
                    learningDisposition: "replay_strict_same_provider_positive_program",
                  }
                : {
                    ...baseRepairTarget,
                    scope: "learning",
                    repairType: "evolved_strategy",
                    engine: "brain_learning_lab",
                    pipelineStage: "learning",
                    profiles: [postExhaustionHint.profile],
                    learningDisposition: "execute_bounded_evolved_strategy",
                  }
            )
          : learningMode
            ? {
                ...baseRepairTarget,
                scope: "learning",
                repairType: "architecture_gap",
                engine: "brain_learning_lab",
                pipelineStage: "learning",
                profiles: [],
                learningDisposition: "propose_new_or_evolved_core_type",
              }
            : {
                ...baseRepairTarget,
                scope: "deferred",
                repairType: "experiment_strategy_exhausted",
                engine: "independent_learning_queue",
                pipelineStage: "deferred_learning",
                profiles: [],
                learningDisposition: "queue_new_strategy_after_variant_exhaustion",
              }
      )
    : baseRepairTarget;
  // A strict same-provider positive program is stronger evidence than an
  // advisory hypothesis. Once selected as the production rescue, it owns the
  // bounded attempt and the LLM advisor must not re-open a mixed execution set.
  const llmAdvisorHint = (
    !providerPositiveProgramProductionRescue
    && (!experimentExhausted || !learningMode)
  )
    ? llmAdvisorStrategyHint(
        providerId,
        evidence.failureClass,
        allMemoryMatches,
        rotateEvery,
      )
    : { profile: "", strategy: "", confidence: 0, experiment: {}, experimentFingerprint: "" };
  const llmAdvisorProductionRescue = (
    !learningMode
    && experimentExhausted
    && Boolean(llmAdvisorHint.profile)
  );
  const historicalHint = (
    !experimentExhausted
    && learningMode
    && experimentVariant >= Math.max(1, finalVariant - 1)
  )
    ? historicalStrategyHint(
        providerId,
        evidence.failureClass,
        experimentGeneration,
        allMemoryMatches,
        rotateEvery,
      )
    : { profile: "", caseId: "", solutionClass: "" };
  const effectiveRepairTarget = llmAdvisorProductionRescue
    ? baseRepairTarget
    : repairTarget;
  const causalProfile = strategyEscalated
    ? postExhaustionHint.profile
    : (
        llmAdvisorHint.profile
        || (
          experimentExhausted
            ? ""
            : (
                historicalHint.profile
                || causalStrategyProfile(
                  evidence.failureClass,
                  experimentVariant,
                  experimentGeneration,
                  finalVariant,
                )
              )
        )
      );
  const executionRepairTarget = causalProfile
    ? {
        ...effectiveRepairTarget,
        profiles: [
          causalProfile,
          ...stringArray(effectiveRepairTarget.profiles).filter((profile) => profile !== "adaptive_runtime_recovery" && profile !== causalProfile),
        ],
      }
    : effectiveRepairTarget;
  const effectiveAction = (strategyEscalated || llmAdvisorProductionRescue)
    ? "probe-targeted-repair"
    : experimentExhausted
      ? (learningMode ? "collect-more-evidence" : "deferred_retry")
      : stringValue(plan.action, "deferred_retry");
  const effectiveExitReason = (strategyEscalated || llmAdvisorProductionRescue)
    ? null
    : experimentExhausted
      ? (learningMode ? "learning_generations_exhausted" : "experiment_variants_exhausted")
      : plan.exitReason ?? null;
  const effectiveHypotheses = (
    experimentExhausted
    && !strategyEscalated
    && !llmAdvisorProductionRescue
  ) ? [] : hypotheses;
  return {
    brainVersion: finiteNumber(plan.brainVersion, BRAIN_CONTROL_PLANE_VERSION),
    providerId,
    failureClass: stringValue(plan.failureClass, "unknown_failure"),
    repairScope: effectiveRepairTarget.scope,
    repairType: effectiveRepairTarget.repairType,
    repairEngine: effectiveRepairTarget.engine,
    pipelineStage: effectiveRepairTarget.pipelineStage,
    observedPipelineStage: stringValue(evidence.observedPipelineStage, "unknown"),
    censusStatus: stringValue(asRecord(candidate.censusPrior).status),
    censusPriorApplied: evidence.censusPriorApplied === true,
    censusPriorReason: stringValue(evidence.censusPriorReason),
    negativeMemoryMatches,
    experimentVariant,
    experimentGeneration,
    baseExperimentExhausted: experimentExhausted,
    experimentExhausted: experimentExhausted && !strategyEscalated && !llmAdvisorProductionRescue,
    strategyEscalated,
    providerPositiveProgramReplay: postExhaustionHint.profile === "provider_positive_program_replay_v1",
    positiveProgramFingerprint: stringValue(postExhaustionHint.positiveProgramFingerprint).toLowerCase(),
    strategyImplementationFingerprint: stringValue(postExhaustionHint.strategyImplementationFingerprint).toLowerCase(),
    postExhaustionStrategyProfile: postExhaustionHint.profile,
    postExhaustionStrategyMethod: postExhaustionHint.method,
    postExhaustionStrategyIndex: postExhaustionHint.index,
    experimentRotationEvery: rotateEvery,
    experimentVariantCount: maxVariants,
    experimentGenerationLimit: learningMode ? maxLearningGenerations : finalVariantGeneration,
    llmAdvisorApplied: Boolean(llmAdvisorHint.profile),
    llmAdvisorRescue: llmAdvisorProductionRescue,
    providerPositiveProgramProductionRescue,
    llmAdvisorStrategy: llmAdvisorHint.strategy,
    llmAdvisorProfile: llmAdvisorHint.profile,
    llmAdvisorConfidence: llmAdvisorHint.confidence,
    llmAdvisorSourceFailureClass: llmAdvisorHint.sourceFailureClass,
    llmAdvisorFailureCompatibility: llmAdvisorHint.failureCompatibility,
    llmAdvisorExperiment: llmAdvisorHint.experiment,
    llmAdvisorExperimentFingerprint: llmAdvisorHint.experimentFingerprint,
    historicalStrategyProfile: historicalHint.profile,
    historicalStrategyCase: historicalHint.caseId,
    historicalSolutionClass: historicalHint.solutionClass,
    learningDisposition: effectiveRepairTarget.learningDisposition,
    capabilityStrategy,
    signature,
    action: effectiveAction,
    exitReason: effectiveExitReason,
    hypotheses: effectiveHypotheses.map((row) => ({
      id: stringValue(row.id),
      capabilities: stringArray(row.capabilities),
      clientVersions: asRecord(row.clientVersions ?? row.runtimeVersions),
      actions: stringArray(row.actions),
      profile: stringValue(row.profile) || null,
      learned: row.learned === true,
      maturity: row.maturity ?? null,
      transferScore: finiteNumber(row.transferScore, 0),
      confidence: finiteNumber(row.confidence, 0),
    })).filter((row) => row.id),
    allowedProfiles: profilesForRepairTarget({ ...plan, action: effectiveAction, hypotheses: effectiveHypotheses }, executionRepairTarget),
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

function learnedSkillTransferEligible(skill) {
  if (skill.validated !== true) return false;
  if (stringValue(skill.maturity, "experimental") !== stringValue(skillTransfer.maturity, "trusted")) return false;
  const minimumConfidence = finiteNumber(skillTransfer.minimumConfidence, finiteNumber(maturity.minimumConfidence, 0.8));
  const minimumProviders = Math.max(1, finiteNumber(skillTransfer.minimumDistinctProviders, finiteNumber(maturity.trustedProviders, 2)));
  if (finiteNumber(skill.confidence, 0) < minimumConfidence) return false;
  if (stringArray(skill.providers).length < minimumProviders) return false;
  return true;
}

function learnedSkillTransferScore({
  providerId, signature, capabilityStrategy, observedPipelineStage,
  providers, signatures, strategies, stages, confidence, successCount, failureCount,
  sameProviderPositiveProgram = false,
}) {
  let score = finiteNumber(skillTransfer.genericFailureClassBase, 15);
  if (sameProviderPositiveProgram) {
    // Provider-local strict positive proof outranks exploratory/global priors
    // for that same provider in Repair or Learning. It remains a candidate only:
    // current-byte playback, identity and non-regression gates still decide.
    score += finiteNumber(skillTransfer.sameProviderPositiveProgramBonus, 1000);
  }
  if (signature && signatures.includes(signature)) score += finiteNumber(skillTransfer.exactSignatureBonus, 100);
  if (capabilityStrategy && strategies.includes(capabilityStrategy)) score += finiteNumber(skillTransfer.capabilityStrategyBonus, 40);
  if (observedPipelineStage && stages.includes(String(observedPipelineStage).toLowerCase())) score += finiteNumber(skillTransfer.observedStageBonus, 20);
  if (providerId && providers.includes(providerId)) score += finiteNumber(skillTransfer.providerPriorBonus, 10);
  score += Math.round(Math.max(0, Math.min(1, confidence)) * 20);
  score += Math.min(20, Math.max(0, successCount) * 2);
  score -= Math.max(0, failureCount) * finiteNumber(skillTransfer.failedSkillPenalty, 12);
  return score;
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
  if (
    repairTarget.scope !== "capability"
    && stringValue(repairTarget.repairType) !== "evolved_strategy"
  ) return [];
  const transferred = asArray(plan.hypotheses)
    .filter((row) => isRecord(row) && row.learned === true)
    .sort((a, b) => finiteNumber(b.transferScore, 0) - finiteNumber(a.transferScore, 0))
    .map((row) => stringValue(row.profile))
    .filter(Boolean);
  const explicit = stringArray(repairTarget.profiles);
  // An explicitly selected evolved strategy is the causal experiment being
  // tested now. A strict same-provider positive replay is even narrower: its
  // exact program fingerprint owns this attempt, so generic learned fallbacks
  // must not share the same bounded experiment and blur attribution.
  if (stringValue(repairTarget.learningDisposition) === "replay_strict_same_provider_positive_program") {
    return [...new Set(explicit)];
  }
  return stringValue(repairTarget.repairType) === "evolved_strategy"
    ? [...new Set([...explicit, ...transferred])]
    : [...new Set([...transferred, ...explicit])];
}

function applyCensusPrior(rawEvidence, candidate) {
  const evidence = { ...asRecord(rawEvidence) };
  const prior = asRecord(candidate.censusPrior);
  const status = stringValue(prior.status).toUpperCase();
  if (!status) return evidence;

  const currentFailure = classifyFailure(evidence);
  const currentStage = stringValue(evidence.observedPipelineStage, "unknown").toLowerCase();
  const safetyOrSuccess = new Set([
    "healthy", "identity_mismatch", "structured_parse_gap", "runtime_contract_drift",
    "media_validation_gap", "playback_context_gap", "playback_http_access",
    "playback_http_gone", "playback_rate_limited", "playback_http_upstream",
    "playback_http_response", "playback_timeout", "playback_dns", "playback_tls",
    "playback_parser", "playback_decoder", "playback_io", "playback_live_window",
    "playback_runtime_setup", "playback_player_error", "playback_duration_unknown",
    "short_media", "audio_track_gap",
  ]);
  if (safetyOrSuccess.has(currentFailure)) return evidence;

  const withPrior = (failureClass, stage, reason) => ({
    ...evidence,
    forcedFailureClass: failureClass,
    observedPipelineStage: pipelineStageRank(stage) > pipelineStageRank(currentStage) ? stage : currentStage,
    censusPriorApplied: true,
    censusPriorReason: reason,
  });

  if (status === "CHAIN REACHED") {
    // Census is a floor, never a ceiling. Once the current bytes reproduce the
    // historical player depth, let fresher causal evidence (for example
    // media_extraction_gap) drive the next repair instead of pinning the
    // provider forever to chain_terminal_gap.
    if (pipelineStageRank(currentStage) >= pipelineStageRank("player")) return evidence;
    return withPrior(
      "chain_terminal_gap",
      "player",
      "census_chain_reached_forbids_regression_to_search_or_detail",
    );
  }
  if (status === "ROUTE PROVEN") {
    if (pipelineStageRank(currentStage) >= pipelineStageRank("detail")) return evidence;
    return withPrior(
      "route_proven_gap",
      "detail",
      "census_route_proof_forbids_rediscovering_search",
    );
  }
  if (status === "CANDIDATE OK") {
    if (currentFailure === "transport_blocked" || currentFailure === "dns_unreachable") return evidence;
    if (pipelineStageRank(currentStage) >= pipelineStageRank("player")) return evidence;
    return withPrior(
      "candidate_replay_gap",
      "player",
      "census_candidate_playback_requires_current_byte_reproduction",
    );
  }
  if (status === "PROVIDER NETWORK BLOCKED") {
    // A fresh successful provider-stage request supersedes yesterday's negative
    // transport diagnosis. Keep the historical status as census context, but
    // do not drag a now-reachable provider back to the transport layer.
    if (pipelineStageRank(currentStage) >= pipelineStageRank("search")) return evidence;
    return withPrior(
      "provider_transport_gap",
      currentStage === "unknown" ? "source" : currentStage,
      "census_network_block_requires_transport_before_parser_mutation",
    );
  }
  return evidence;
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
