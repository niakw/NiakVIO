const HTTP_BLOCKED = new Set([401, 403, 407, 429, 451]);
const HTTP_GONE = new Set([404, 410]);

export const FAILURE_CLASSES = Object.freeze([
  "healthy",
  "not_invoked",
  "dns_unreachable",
  "transport_blocked",
  "search_gap",
  "identity_mismatch",
  "detail_gap",
  "episode_gap",
  "player_gap",
  "media_extraction_gap",
  "playback_context_gap",
  "media_validation_gap",
  "runtime_contract_drift",
  "unknown_failure",
]);

export const REPAIR_RECIPES = Object.freeze({
  not_invoked: [
    recipe("inspect-runtime-call-contract", ["invocation", "media-type", "settings"], ["verify getStreams positional contract", "normalize media type before provider call", "verify runtime settings injection"]),
    recipe("probe-provider-entrypoint", ["invocation"], ["execute provider with canonical request", "record first provider-origin request"]),
  ],
  dns_unreachable: [
    recipe("resolve-official-hub-domain", ["dns", "hub"], ["check declared official hub", "follow official redirects", "compare known upstream domains"]),
    recipe("probe-lkg-domain", ["dns", "lkg"], ["test last-known-good domain without publishing it blindly"]),
  ],
  transport_blocked: [
    recipe("bootstrap-session", ["headers", "cookies", "redirects"], ["load provider landing page", "preserve cookies", "preserve redirect chain", "retry exact route with browser-compatible headers"]),
    recipe("alternate-official-route", ["routes", "hub"], ["discover current official API/search route", "avoid cross-provider fallback"]),
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
    recipe("discover-player-chain", ["player", "embed"], ["inspect iframe/player links", "inspect scripts and XHR", "follow provider-owned player chain"]),
  ],
  media_extraction_gap: [
    recipe("capture-media-network", ["media", "xhr", "json"], ["inspect player XHR/fetch", "extract HLS/DASH/direct candidates", "keep player provenance"]),
    recipe("inspect-player-javascript", ["media", "javascript"], ["identify deobfuscation/token generation", "reproduce only required deterministic logic"]),
  ],
  playback_context_gap: [
    recipe("preserve-playback-context", ["headers", "cookies", "referer", "origin"], ["carry Referer from player chain", "carry Origin when required", "carry scoped cookies", "preserve redirects and final URL"]),
    recipe("refresh-media-token", ["token", "session"], ["re-enter player chain", "obtain fresh media token", "avoid persisting expired signed URLs"]),
  ],
  media_validation_gap: [
    recipe("validate-final-media", ["media", "identity"], ["probe final media response", "verify media identity and duration", "verify HLS/DASH structure", "reject HTML/error bodies"]),
  ],
  runtime_contract_drift: [
    recipe("reaudit-device-adapter", ["runtime-version", "contract"], ["diff changed Nuvio contract paths", "identify affected capabilities", "revalidate only impacted recipes/providers"]),
  ],
  unknown_failure: [
    recipe("collect-missing-evidence", ["evidence"], ["find first unobserved pipeline stage", "probe that stage only", "reclassify before repair"]),
  ],
});

export function classifyFailure(evidence = {}) {
  if (evidence.contractDrift === true) return "runtime_contract_drift";
  if (evidence.suspicious === true || evidence.unsafe === true) return "identity_mismatch";
  if (evidence.invoked === false) return "not_invoked";
  if (evidence.dns?.ok === false) return "dns_unreachable";

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
  if (media?.found === true && (isBlocked(media?.status) || HTTP_GONE.has(Number(media?.status)))) return "playback_context_gap";
  if (media?.found === true && media?.playable === false) return "media_validation_gap";

  if (Number(evidence.playableStreams ?? 0) > 0 || media?.playable === true) return "healthy";
  return "unknown_failure";
}

export function planRepair(evidence = {}, options = {}) {
  const failureClass = classifyFailure(evidence);
  if (failureClass === "healthy") {
    return { failureClass, hypotheses: [], action: "none" };
  }

  const maxHypotheses = clamp(options.maxHypotheses ?? 3, 1, 3);
  const candidates = [...(REPAIR_RECIPES[failureClass] ?? REPAIR_RECIPES.unknown_failure)];
  const compatible = candidates.filter((candidate) => recipeIsCompatible(candidate, options.runtimeCompatibility));

  return {
    failureClass,
    hypotheses: compatible.slice(0, maxHypotheses),
    action: failureClass === "identity_mismatch" && (evidence.suspicious || evidence.unsafe)
      ? "hold-or-quarantine-pending-proof"
      : "probe-targeted-repair",
  };
}

export function recipeIsCompatible(candidate, runtimeCompatibility = null) {
  if (!runtimeCompatibility) return true;
  const invalidCapabilities = new Set(runtimeCompatibility.invalidCapabilities ?? []);
  return !candidate.capabilities.some((capability) => invalidCapabilities.has(capability));
}

export function buildLearnedRecipe({ id, signature, actions, provenOn, runtime, capabilities = [] }) {
  if (!id || !signature || !Array.isArray(actions) || actions.length === 0) {
    throw new Error("learned recipe requires id, signature and actions");
  }
  return {
    id,
    signature,
    actions: [...actions],
    capabilities: [...new Set(capabilities)],
    provenOn: Array.isArray(provenOn) ? [...provenOn] : [],
    runtime: runtime ?? {},
    learnedAt: new Date().toISOString(),
  };
}

function recipe(id, capabilities, actions) {
  return Object.freeze({ id, capabilities: Object.freeze(capabilities), actions: Object.freeze(actions) });
}

function isSuccess(status) {
  const code = Number(status);
  return code >= 200 && code < 300;
}

function isBlocked(status) {
  return HTTP_BLOCKED.has(Number(status));
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, Number(value)));
}
