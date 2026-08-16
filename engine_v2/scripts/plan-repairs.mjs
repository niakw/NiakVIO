#!/usr/bin/env node
import fs from "node:fs";
import process from "node:process";
import { classifyFailure, planRepair } from "../src/repair-brain.mjs";
import { evidenceSignature } from "../src/recipe-memory.mjs";

const input = JSON.parse(fs.readFileSync(0, "utf8") || "{}");
const policy = input.policy ?? {};
const production = policy.production ?? {};
const maturity = policy.skillMaturity ?? {};
const learnedSkills = normalizeLearnedSkills(input.learnedSkills ?? []);
const output = { schemaVersion: 1, mode: input.mode ?? "quick", plans: {} };

for (const item of input.items ?? []) {
  if (!item?.key) continue;
  const evidence = deriveEvidence(item.candidate ?? {}, item.result ?? {});
  evidence.failureClass = classifyFailure(evidence);
  const signature = evidenceSignature(evidence);
  const providerId = String(item.candidate?.canonical_id ?? item.candidate?.upstream_id ?? "").toLowerCase();
  const reusable = learnedSkills
    .filter((skill) => !skill.failureClass || skill.failureClass === evidence.failureClass || skill.failure_class === evidence.failureClass)
    .filter((skill) => skill.autoApply === true || (skill.providers ?? skill.provenOnProviders ?? []).map((x) => String(x).toLowerCase()).includes(providerId))
    .map((skill) => ({
      id: skill.id,
      failureClass: skill.failureClass ?? skill.failure_class ?? null,
      capabilities: skill.capabilities ?? [],
      actions: skill.actions ?? [`apply learned profile ${skill.profile ?? ""}`],
      profile: skill.profile ?? null,
      learned: true,
      maturity: skill.maturity ?? "experimental",
    }));

  const plan = planRepair(evidence, {
    signature,
    learnedSkills: reusable,
    maxHypotheses: production.maxHypotheses ?? 3,
    budget: {
      maxHypotheses: production.maxHypotheses ?? 3,
      maxMutations: production.maxMutationsPerProvider ?? 2,
      maxRepeatedSignature: production.maxRepeatedSignature ?? 2,
      maxGeneratedBytes: production.maxGeneratedBytesPerProvider ?? 180000,
      maxElapsedMs: production.maxElapsedMsPerProvider ?? 45000,
      mutationCount: Number(item.state?.mutationCount ?? 0),
      repeatedSignatureCount: Number(item.state?.repeatedSignatureCount ?? 0),
      generatedBytes: Number(item.state?.generatedBytes ?? 0),
      elapsedMs: Number(item.state?.elapsedMs ?? 0),
    },
    learningLab: input.mode === "learning",
    coreMutationRequested: item.state?.coreMutationRequested === true,
  });
  const allowedProfiles = profilesForPlan(plan, reusable);
  output.plans[item.key] = {
    providerId,
    failureClass: plan.failureClass,
    signature,
    action: plan.action,
    exitReason: plan.exitReason ?? null,
    hypotheses: plan.hypotheses.map((row) => ({
      id: row.id,
      capabilities: row.capabilities ?? [],
      actions: row.actions ?? [],
      learned: row.learned === true,
      maturity: row.maturity ?? null,
    })),
    allowedProfiles,
    budget: plan.budget,
    fallbackPolicy: plan.fallbackPolicy,
    coreMutationPolicy: plan.coreMutationPolicy,
    skillPolicy: maturity,
  };
}

process.stdout.write(JSON.stringify(output));

function normalizeLearnedSkills(value) {
  if (Array.isArray(value)) return value;
  if (value && typeof value === "object") return Object.values(value);
  return [];
}

function profilesForPlan(plan, learned) {
  if (!["probe-targeted-repair"].includes(plan.action)) return [];
  const profiles = [];
  for (const skill of learned) {
    if (skill.profile && plan.hypotheses.some((row) => row.id === skill.id)) profiles.push(skill.profile);
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
  };
  for (const hypothesis of plan.hypotheses) {
    for (const profile of map[hypothesis.id] ?? []) profiles.push(profile);
  }
  return [...new Set(profiles)];
}

function deriveEvidence(candidate, result) {
  const status = String(result.status ?? "runtime_error");
  const tests = Array.isArray(result.tests) ? result.tests : [];
  const evidence = result.evidence ?? {};
  const playable = Number(evidence.streams_playable ?? Math.max(0, ...tests.map((row) => Number(row.streams_playable ?? 0))));
  const returned = Number(evidence.streams_returned ?? Math.max(0, ...tests.map((row) => Number(row.stream_count ?? row.streams_returned ?? 0))));
  const failureText = tests.map((row) => `${row.failure_class ?? ""} ${row.status ?? ""} ${row.error_details?.code ?? ""} ${row.error_details?.message ?? ""}`).join(" ").toLowerCase();
  const observations = tests.flatMap((row) => Array.isArray(row.network_observations) ? row.network_observations : []);
  const statuses = observations.map((row) => Number(row.status)).filter(Number.isFinite);
  const providerStatuses = observations.filter((row) => !row.infrastructure).map((row) => Number(row.status)).filter(Number.isFinite);
  const blocked = providerStatuses.find((code) => [401, 403, 407, 429, 451].includes(code));
  const gone = providerStatuses.find((code) => [404, 410].includes(code));
  const mediaType = String(tests[0]?.fixture?.category ?? tests[0]?.fixture?.mediaType ?? candidate.metadata?.supportedTypes?.[0] ?? "movie").toLowerCase();
  const identityContradiction = Number(evidence.identity_contradiction_count ?? 0) > 0 || Number(evidence.duration_identity_mismatch_count ?? 0) > 0 || /identity|duration.*mismatch/.test(failureText);
  const invoked = !/not[_ -]?invoked|invalid[_ -]?request[_ -]?argument|object%20object|object object/.test(failureText);
  const contractDrift = status === "runtime_error" && /invalid[_ -]?request[_ -]?argument|object%20object|object object|signature|argument/.test(failureText);

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
