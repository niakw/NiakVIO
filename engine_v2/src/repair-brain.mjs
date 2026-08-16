const HTTP_BLOCKED = new Set([401, 403, 407, 429, 451]);
const HTTP_GONE = new Set([404, 410]);
export const BRAIN_CONTROL_PLANE_VERSION = 2;

export const FAILURE_CLASSES = Object.freeze([
  "healthy", "not_invoked", "dns_unreachable", "transport_blocked", "search_gap",
  "identity_mismatch", "detail_gap", "episode_gap", "player_gap",
  "media_extraction_gap", "playback_context_gap", "media_validation_gap",
  "runtime_contract_drift", "unknown_failure",
]);

export const REPAIR_RECIPES = Object.freeze({
  not_invoked: [
    recipe("inspect-runtime-call-contract", ["invocation", "media-type", "settings"], ["verify getStreams positional contract", "normalize media type before provider call", "verify runtime settings injection"]),
    recipe("probe-provider-entrypoint", ["invocation"], ["execute provider with canonical request", "record first provider-origin request"]),
  ],
  dns_unreachable: [
    recipe("resolve-official-hub-domain", ["dns", "hub", "search", "telegram"], ["check declared official hub", "search public address sources when known routes fail", "prefer latest relevant Telegram message id", "validate terminal before retention"]),
    recipe("probe-lkg-domain", ["dns", "lkg"], ["test last-known-good domain without publishing it blindly"]),
  ],
  transport_blocked: [
    recipe("bootstrap-session", ["headers", "cookies", "redirects"], ["load provider landing page", "preserve cookies", "preserve redirect chain", "retry exact route with browser-compatible headers"]),
    recipe("alternate-official-route", ["routes", "hub", "search", "telegram"], ["discover current official site/API/search route", "avoid cross-provider fallback"]),
  ],
  search_gap: [
    recipe("rediscover-search-route", ["search", "routes"], ["inspect forms/XHR/JSON", "derive query encoding", "probe title and TMDB-aware variants"]),
    recipe("repair-search-parser", ["search", "parser"], ["inspect returned HTML/JSON", "update result selectors/keys", "retain identity evidence"]),
  ],
  identity_mismatch: [
    recipe("tighten-identity-match", ["identity"], ["require correct title/TMDB/year", "require correct season/episode when episodic", "reject near-title collisions"]),
  ],
  detail_gap: [
    recipe("repair-detail-resolution", ["detail", "parser"], ["inspect result href/id", "follow canonical detail URL", "use structured data before brittle selectors"]),
  ],
  episode_gap: [
    recipe("repair-series-navigation", ["series", "episode"], ["inspect season route/data", "map canonical season/episode", "verify selected episode identity"]),
    recipe("repair-anime-episode-mapping", ["anime", "episode"], ["inspect absolute-vs-season episode numbering", "verify requested episode identity"]),
  ],
  player_gap: [
    recipe("discover-player-chain", ["player", "embed", "html"], ["traverse catalogue/detail/embed rather than requiring an API", "inspect iframe/player links", "inspect scripts and XHR", "follow the player chain to a terminal media candidate"]),
  ],
  media_extraction_gap: [
    recipe("capture-media-network", ["media", "xhr", "json"], ["inspect player XHR/fetch", "extract HLS/DASH/direct candidates", "keep player provenance"]),
    recipe("inspect-player-javascript", ["media", "javascript"], ["identify deterministic token/deobfuscation logic", "reproduce only the required logic"]),
  ],
  playback_context_gap: [
    recipe("preserve-playback-context", ["headers", "cookies", "referer", "origin"], ["carry Referer from player chain", "carry Origin when required", "carry scoped cookies", "preserve redirects and final URL"]),
    recipe("refresh-media-token", ["token", "session"], ["re-enter player chain", "obtain fresh media token", "avoid persisting expired signed URLs"]),
  ],
  media_validation_gap: [
    recipe("validate-final-media", ["media", "identity"], ["probe final media response", "verify media identity and duration", "verify HLS/DASH/direct signatures", "reject HTML/error bodies and fake media"]),
  ],
  runtime_contract_drift: [
    recipe("reaudit-device-adapter", ["runtime-version", "contract"], ["diff changed Nuvio contract paths", "identify affected capabilities", "revalidate only impacted skills/providers"]),
  ],
  unknown_failure: [
    recipe("collect-missing-evidence", ["evidence"], ["find first unobserved pipeline stage", "probe that stage only", "reclassify before mutating provider code"]),
  ],
});

export function classifyFailure(evidence = {}) {
  if (evidence.contractDrift === true) return "runtime_contract_drift";
  if (evidence.suspicious === true || evidence.unsafe === true) return "identity_mismatch";
  if (evidence.invoked === false) return "not_invoked";
  if (evidence.dns?.ok === false || evidence.stages?.dns?.ok === false) return "dns_unreachable";
  const homepage = evidence.stages?.homepage;
  if (isBlocked(homepage?.status)) return "transport_blocked";
  const search = evidence.stages?.search;
  if (isBlocked(search?.status)) return "transport_blocked";
  if (search?.attempted && isSuccess(search?.status) && Number(search?.matches ?? 0) === 0) return "search_gap";
  const identity = evidence.stages?.identity;
  if (identity?.attempted && identity?.matched === false) return "identity_mismatch";
  const detail = evidence.stages?.detail;
  if (detail?.attempted && detail?.found === false) return "detail_gap";
  const requestType = String(evidence.request?.mediaType ?? "").toLowerCase();
  const episode = evidence.stages?.episode;
  if ((requestType === "tv" || requestType === "anime") && episode?.attempted && episode?.found === false) return "episode_gap";
  const player = evidence.stages?.player;
  if (player?.attempted && player?.found === false) return "player_gap";
  const media = evidence.stages?.media;
  if (media?.attempted && media?.found === false) return "media_extraction_gap";
  const validation = evidence.stages?.validation;
  if (validation?.attempted) {
    const statuses = new Set((validation.statuses ?? []).map(Number));
    if ([...statuses].some((status) => HTTP_BLOCKED.has(status) || HTTP_GONE.has(status))) return "playback_context_gap";
    if (validation.playable === false || Number(validation.playableCount ?? 0) === 0) return "media_validation_gap";
  }
  if (Number(evidence.playableStreams ?? 0) > 0 || validation?.playable === true) return "healthy";
  if (media?.found === true && validation?.observed !== true) return "media_validation_gap";
  return "unknown_failure";
}

export function planRepair(evidence = {}, options = {}) {
  const failureClass = classifyFailure(evidence);
  const signature = String(options.signature ?? evidence.signature ?? "");
  const budget = normalizedBudget(options.budget ?? options);
  const exitReason = budgetExitReason({ ...budget, signature });
  if (failureClass === "healthy") return planResult(failureClass, [], "none", budget, null);
  if (failureClass === "identity_mismatch" && (evidence.suspicious || evidence.unsafe)) {
    return planResult(failureClass, [], "hold-or-quarantine-pending-proof", budget, null);
  }
  if (exitReason) return planResult(failureClass, [], "deferred_retry", budget, exitReason);
  if (options.coreMutationRequested === true && options.learningLab !== true) {
    return planResult(failureClass, [], "deferred_retry", budget, "core_mutation_requires_learning_lab");
  }

  const learned = Array.isArray(options.learnedSkills) ? options.learnedSkills : [];
  const candidates = [
    ...learned.filter((skill) => !skill.failureClass || skill.failureClass === failureClass),
    ...(REPAIR_RECIPES[failureClass] ?? REPAIR_RECIPES.unknown_failure),
  ];
  const compatible = uniqueRecipes(candidates)
    .filter((candidate) => recipeIsCompatible(candidate, options.runtimeCompatibility));
  const hypotheses = compatible.slice(0, budget.maxHypotheses);
  const action = failureClass === "unknown_failure" ? "collect-more-evidence" : "probe-targeted-repair";
  return planResult(failureClass, hypotheses, action, budget, null);
}

export function recipeIsCompatible(candidate, runtimeCompatibility = null) {
  if (!runtimeCompatibility) return true;
  const invalidCapabilities = new Set(runtimeCompatibility.invalidCapabilities ?? []);
  return !(candidate.capabilities ?? []).some((capability) => invalidCapabilities.has(capability));
}

export function buildLearnedRecipe({ id, signature, actions, provenOn, runtime, capabilities = [], failureClass = null, scope = {} }) {
  if (!id || !signature || !Array.isArray(actions) || actions.length === 0) {
    throw new Error("learned recipe requires id, signature and actions");
  }
  return {
    id, signature, failureClass, actions: [...actions],
    capabilities: [...new Set(capabilities)],
    provenOn: Array.isArray(provenOn) ? [...provenOn] : [],
    scope: structuredClone(scope), runtime: runtime ?? {},
    learnedAt: new Date().toISOString(),
  };
}

function planResult(failureClass, hypotheses, action, budget, exitReason) {
  return {
    brainVersion: BRAIN_CONTROL_PLANE_VERSION,
    failureClass, hypotheses, action, exitReason,
    budget: {
      maxHypotheses: budget.maxHypotheses,
      maxMutations: budget.maxMutations,
      maxRepeatedSignature: budget.maxRepeatedSignature,
      maxGeneratedBytes: budget.maxGeneratedBytes,
      maxElapsedMs: budget.maxElapsedMs,
    },
    fallbackPolicy: "lkg_only_after_repair_budget",
    coreMutationPolicy: "proposal_only",
  };
}

function normalizedBudget(options = {}) {
  return {
    maxHypotheses: clamp(options.maxHypotheses ?? 3, 1, 3),
    maxMutations: clamp(options.maxMutations ?? 2, 0, 8),
    mutationCount: Math.max(0, Number(options.mutationCount ?? 0)),
    maxRepeatedSignature: clamp(options.maxRepeatedSignature ?? 2, 1, 5),
    repeatedSignatureCount: Math.max(0, Number(options.repeatedSignatureCount ?? 0)),
    maxGeneratedBytes: Math.max(0, Number(options.maxGeneratedBytes ?? 180000)),
    generatedBytes: Math.max(0, Number(options.generatedBytes ?? 0)),
    maxElapsedMs: Math.max(1000, Number(options.maxElapsedMs ?? 45000)),
    elapsedMs: Math.max(0, Number(options.elapsedMs ?? 0)),
  };
}

function budgetExitReason(budget) {
  if (budget.mutationCount >= budget.maxMutations) return "mutation_budget_exhausted";
  if (budget.repeatedSignatureCount >= budget.maxRepeatedSignature) return "repair_loop_detected";
  if (budget.generatedBytes >= budget.maxGeneratedBytes) return "generated_code_budget_exhausted";
  if (budget.elapsedMs >= budget.maxElapsedMs) return "time_budget_exhausted";
  return null;
}

function recipe(id, capabilities, actions) {
  return Object.freeze({ id, capabilities: Object.freeze(capabilities), actions: Object.freeze(actions) });
}
function uniqueRecipes(rows) {
  const seen = new Set();
  return rows.filter((row) => row?.id && !seen.has(row.id) && seen.add(row.id));
}
function isSuccess(status) { const code = Number(status); return code >= 200 && code < 300; }
function isBlocked(status) { return HTTP_BLOCKED.has(Number(status)); }
function clamp(value, min, max) { return Math.min(max, Math.max(min, Number(value))); }
