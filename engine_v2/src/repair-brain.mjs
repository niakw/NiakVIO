const HTTP_BLOCKED = new Set([401, 403, 407, 429, 451]);
const HTTP_GONE = new Set([404, 410]);
export const BRAIN_CONTROL_PLANE_VERSION = 4;

export const FAILURE_CLASSES = Object.freeze([
  "healthy", "not_invoked", "dns_unreachable", "transport_blocked", "search_gap",
  "identity_mismatch", "detail_gap", "episode_gap", "player_gap",
  "media_extraction_gap", "playback_context_gap", "media_validation_gap",
  "playback_http_access", "playback_http_gone", "playback_rate_limited",
  "playback_http_upstream", "playback_http_response", "playback_timeout",
  "playback_dns", "playback_tls", "playback_parser", "playback_decoder",
  "playback_io", "playback_live_window", "playback_runtime_setup",
  "playback_player_error", "playback_duration_unknown", "short_media",
  "structured_parse_gap", "runtime_contract_drift", "unknown_failure",
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
  detail_gap: [recipe("repair-detail-resolution", ["detail", "parser"], ["inspect result href/id", "follow canonical detail URL", "use structured data before brittle selectors"])],
  episode_gap: [
    recipe("repair-series-navigation", ["series", "episode"], ["inspect season route/data", "map canonical season/episode", "verify selected episode identity"]),
    recipe("repair-anime-episode-mapping", ["anime", "episode"], ["inspect absolute-vs-season episode numbering", "verify requested episode identity"]),
  ],
  player_gap: [recipe("discover-player-chain", ["player", "embed", "html"], ["traverse catalogue/detail/embed rather than requiring an API", "inspect iframe/player links", "inspect scripts and XHR", "follow the player chain to a terminal media candidate"])],
  media_extraction_gap: [
    recipe("capture-media-network", ["media", "xhr", "json"], ["inspect player XHR/fetch", "extract HLS/DASH/direct candidates", "keep player provenance"]),
    recipe("inspect-player-javascript", ["media", "javascript"], ["identify deterministic token/deobfuscation logic", "reproduce only the required logic"]),
  ],
  playback_context_gap: [
    recipe("preserve-playback-context", ["headers", "cookies", "referer", "origin"], ["carry Referer from player chain", "carry Origin when required", "carry scoped cookies", "preserve redirects and final URL"]),
    recipe("refresh-media-token", ["token", "session"], ["re-enter player chain", "obtain fresh media token", "avoid persisting expired signed URLs"]),
  ],
  playback_http_access: [
    recipe("replay-native-request-context", ["headers", "cookies", "referer", "origin", "redirects"], ["compare provider output context with native reader request", "preserve only required request headers", "preserve scoped cookies and redirect context", "retry through the same official client networking stack"]),
    recipe("refresh-access-bound-media", ["token", "session", "player"], ["re-enter the player chain", "refresh signed or session-bound media", "reject stale terminal URLs"]),
  ],
  playback_http_gone: [recipe("refresh-terminal-media-candidate", ["player", "media", "token"], ["re-enter current player page", "resolve a fresh terminal candidate", "do not retain dead media URLs"])],
  playback_rate_limited: [recipe("respect-media-rate-limit", ["session", "timing"], ["avoid duplicate pre-consumption", "reuse established session", "back off before one targeted native-reader retry"])],
  playback_http_upstream: [recipe("retry-or-rerank-upstream-media", ["media", "ranking"], ["confirm upstream server failure in native reader", "try next same-provider candidate", "deprioritize repeatedly failing host without cross-provider substitution"])],
  playback_http_response: [recipe("inspect-unexpected-media-response", ["media", "headers"], ["record status and response header names", "verify redirects/content-disposition/content-type", "resolve a terminal media response the reader accepts"])],
  playback_timeout: [recipe("diagnose-native-reader-timeout", ["timeout", "media", "range"], ["separate connect/read/segment timeout evidence", "verify range behavior", "try next same-provider stream when terminal host stalls"])],
  playback_dns: [recipe("repair-media-host-resolution", ["dns", "media"], ["resolve terminal media host from OS environment", "refresh stale host from player chain", "avoid hardcoded dead CDN hosts"])],
  playback_tls: [recipe("repair-media-tls-path", ["tls", "media"], ["capture TLS/handshake class from native reader", "verify official client networking policy", "refresh terminal host when certificate/SNI target is stale"])],
  playback_parser: [recipe("resolve-real-media-not-wrapper", ["parser", "media", "html"], ["reject HTML/JSON/error wrappers presented as media", "follow embed/download chain further", "require reader-parseable HLS/DASH/container before promotion"])],
  playback_decoder: [recipe("rerank-reader-compatible-encoding", ["decoder", "codec", "media"], ["record Media3 decoder error code", "prefer another same-provider rendition/container", "do not mutate transport context for a codec-only failure"])],
  playback_io: [recipe("repair-reader-io-contract", ["range", "headers", "media"], ["inspect Range/Accept-Ranges/content-length behavior", "preserve reader-required headers", "distinguish server refusal from parser or decoder failure"])],
  playback_live_window: [recipe("refresh-live-window", ["media", "playlist"], ["reload current manifest", "avoid stale media sequence", "retry only the refreshed live candidate"])],
  playback_runtime_setup: [recipe("repair-native-reader-setup", ["runtime-version", "contract"], ["verify official client data-source factory can be constructed", "diff accepted client revision", "treat setup failure as lab/runtime defect before provider mutation"])],
  playback_player_error: [recipe("inspect-native-player-error-chain", ["player", "evidence"], ["retain sanitized PlaybackException code/class chain", "classify the first causal layer", "do not mutate provider until the error is reclassified"])],
  playback_duration_unknown: [recipe("prove-vod-duration-before-promotion", ["duration", "media", "identity"], ["wait for the native reader timeline to settle", "derive VOD duration from reader, manifest or container metadata", "reject promotion when long-form duration still cannot be proven"])],
  short_media: [recipe("reject-short-or-preview-media", ["duration", "identity", "ranking"], ["compare reader duration with fixture expectation", "reject previews/trailers/20-second placeholders", "advance to the next same-provider candidate and validate again"])],
  media_validation_gap: [recipe("validate-final-media", ["media", "identity"], ["probe final media response", "verify media identity and duration", "verify HLS/DASH/direct signatures", "reject HTML/error bodies and fake media"])],
  structured_parse_gap: [recipe("repair-structured-parser", ["parser", "json", "javascript"], ["locate destructive pre-parse decoding", "preserve JSON escapes", "retry strict structured parsing", "retain raw fallback when parsing remains ambiguous"])],
  runtime_contract_drift: [recipe("reaudit-device-adapter", ["runtime-version", "contract"], ["diff changed Nuvio contract paths", "identify affected capabilities", "revalidate only impacted skills/providers"])],
  unknown_failure: [recipe("collect-missing-evidence", ["evidence"], ["find first unobserved pipeline stage", "probe that stage only", "reclassify before mutating provider code"])],
});

const READER_STAGE_TO_FAILURE = Object.freeze({
  http_access: "playback_http_access", http_gone: "playback_http_gone", http_rate_limit: "playback_rate_limited",
  http_upstream: "playback_http_upstream", http_response: "playback_http_response", timeout: "playback_timeout",
  dns: "playback_dns", tls: "playback_tls", parser: "playback_parser", decoder: "playback_decoder",
  io: "playback_io", live_window: "playback_live_window", player_setup: "playback_runtime_setup",
  player: "playback_player_error", duration_identity: "short_media", duration_unknown: "playback_duration_unknown",
});

export function classifyFailure(evidence = {}) {
  if (evidence.structuredParseFailure === true) return "structured_parse_gap";
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

  const reader = evidence.stages?.reader ?? evidence.reader;
  if (reader?.attempted || reader?.observed || reader?.state) {
    const explicit = String(reader.failureClass ?? reader.failure_class ?? "");
    if (FAILURE_CLASSES.includes(explicit) && explicit !== "healthy") return explicit;
    const state = String(reader.state ?? "").toLowerCase();
    if (state === "ready" || state === "ended") return "healthy";
    if (state === "short_media") return "short_media";
    if (state === "duration_unknown") return "playback_duration_unknown";
    const stage = String(reader.failureStage ?? reader.failure_stage ?? "").toLowerCase();
    if (READER_STAGE_TO_FAILURE[stage]) return READER_STAGE_TO_FAILURE[stage];
    const status = Number(reader.httpStatus ?? reader.http_status ?? 0);
    if ([401, 403, 407, 451].includes(status)) return "playback_http_access";
    if ([404, 410].includes(status)) return "playback_http_gone";
    if (status === 429) return "playback_rate_limited";
    if (status >= 500 && status <= 599) return "playback_http_upstream";
    if (state === "timeout") return "playback_timeout";
    if (state === "error") return "playback_player_error";
  }

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
  if (failureClass === "identity_mismatch" && (evidence.suspicious || evidence.unsafe)) return planResult(failureClass, [], "hold-or-quarantine-pending-proof", budget, null);
  if (exitReason) return planResult(failureClass, [], "deferred_retry", budget, exitReason);
  if (options.coreMutationRequested === true && options.learningLab !== true) return planResult(failureClass, [], "deferred_retry", budget, "core_mutation_requires_learning_lab");

  const learned = Array.isArray(options.learnedSkills) ? options.learnedSkills : [];
  const candidates = [...learned.filter((skill) => !skill.failureClass || skill.failureClass === failureClass), ...(REPAIR_RECIPES[failureClass] ?? REPAIR_RECIPES.unknown_failure)];
  const compatible = uniqueRecipes(candidates).filter((candidate) => recipeIsCompatible(candidate, options.runtimeCompatibility));
  const hypotheses = compatible.slice(0, budget.maxHypotheses);
  const action = failureClass === "unknown_failure" ? "collect-more-evidence" : "probe-targeted-repair";
  return planResult(failureClass, hypotheses, action, budget, null);
}

export function recipeIsCompatible(candidate, runtimeCompatibility = null) {
  if (!runtimeCompatibility) return true;
  const invalidCapabilities = new Set(runtimeCompatibility.invalidCapabilities ?? []);
  if ((candidate.capabilities ?? []).some((capability) => invalidCapabilities.has(capability))) return false;

  const requirements = candidate.clientVersions ?? candidate.runtimeVersions ?? {};
  const clients = runtimeCompatibility.clients ?? {};
  for (const [clientId, rawRequirement] of Object.entries(requirements)) {
    const requirement = rawRequirement && typeof rawRequirement === "object" ? rawRequirement : {};
    const client = clients[clientId];
    if (!client || typeof client !== "object") return false;
    const supportedMin = Number(client.supportedMinVersionCode ?? client.minVersionCode);
    const supportedMax = Number(client.supportedMaxVersionCode ?? client.maxVersionCode);
    const requiredMin = requirement.min == null ? null : Number(requirement.min);
    const requiredMax = requirement.max == null ? null : Number(requirement.max);
    if (!Number.isFinite(supportedMin) || !Number.isFinite(supportedMax)) return false;
    // A shared provider repair must work for the whole generation range NiakVIO
    // claims to support, not merely for the newest client HEAD used by a Lab run.
    if (requiredMin !== null && (!Number.isFinite(requiredMin) || supportedMin < requiredMin)) return false;
    if (requiredMax !== null && (!Number.isFinite(requiredMax) || supportedMax > requiredMax)) return false;
  }
  return true;
}

export function buildLearnedRecipe({ id, signature, actions, provenOn, runtime, capabilities = [], failureClass = null, scope = {}, clientVersions = {} }) {
  if (!id || !signature || !Array.isArray(actions) || actions.length === 0) throw new Error("learned recipe requires id, signature and actions");
  return { id, signature, failureClass, actions: [...actions], capabilities: [...new Set(capabilities)], provenOn: Array.isArray(provenOn) ? [...provenOn] : [], scope: structuredClone(scope), runtime: runtime ?? {}, clientVersions: structuredClone(clientVersions ?? {}), learnedAt: new Date().toISOString() };
}

function planResult(failureClass, hypotheses, action, budget, exitReason) {
  return { brainVersion: BRAIN_CONTROL_PLANE_VERSION, failureClass, hypotheses, action, exitReason, budget: { maxHypotheses: budget.maxHypotheses, maxMutations: budget.maxMutations, maxRepeatedSignature: budget.maxRepeatedSignature, maxGeneratedBytes: budget.maxGeneratedBytes, maxElapsedMs: budget.maxElapsedMs }, fallbackPolicy: "lkg_only_after_repair_budget", coreMutationPolicy: "proposal_only" };
}
function normalizedBudget(options = {}) {
  return { maxHypotheses: clamp(options.maxHypotheses ?? 3, 1, 3), maxMutations: clamp(options.maxMutations ?? 2, 0, 8), mutationCount: Math.max(0, Number(options.mutationCount ?? 0)), maxRepeatedSignature: clamp(options.maxRepeatedSignature ?? 2, 1, 5), repeatedSignatureCount: Math.max(0, Number(options.repeatedSignatureCount ?? 0)), maxGeneratedBytes: Math.max(0, Number(options.maxGeneratedBytes ?? 180000)), generatedBytes: Math.max(0, Number(options.generatedBytes ?? 0)), maxElapsedMs: Math.max(1000, Number(options.maxElapsedMs ?? 45000)), elapsedMs: Math.max(0, Number(options.elapsedMs ?? 0)) };
}
function budgetExitReason(budget) {
  if (budget.mutationCount >= budget.maxMutations) return "mutation_budget_exhausted";
  if (budget.repeatedSignatureCount >= budget.maxRepeatedSignature) return "repair_loop_detected";
  if (budget.generatedBytes >= budget.maxGeneratedBytes) return "generated_code_budget_exhausted";
  if (budget.elapsedMs >= budget.maxElapsedMs) return "time_budget_exhausted";
  return null;
}
function recipe(id, capabilities, actions) { return Object.freeze({ id, capabilities: Object.freeze(capabilities), actions: Object.freeze(actions) }); }
function uniqueRecipes(rows) { const seen = new Set(); return rows.filter((row) => row?.id && !seen.has(row.id) && seen.add(row.id)); }
function isSuccess(status) { const code = Number(status); return code >= 200 && code < 300; }
function isBlocked(status) { return HTTP_BLOCKED.has(Number(status)); }
function clamp(value, min, max) { return Math.min(max, Math.max(min, Number(value))); }
