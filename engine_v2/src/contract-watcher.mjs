export function classifyChangedPaths(client, files = []) {
  const contractPaths = client.contract_paths ?? [];
  const semanticPaths = client.semantic_paths ?? [];
  const hard = [];
  const semantic = [];
  const unrelated = [];

  for (const file of files) {
    const filename = typeof file === "string" ? file : file.filename;
    if (!filename) continue;
    if (matchesAnyPath(filename, contractPaths)) hard.push(filename);
    else if (matchesAnyPath(filename, semanticPaths)) semantic.push(filename);
    else unrelated.push(filename);
  }

  return { hard, semantic, unrelated };
}

export function classifySemanticTokens(patches = [], tokens = []) {
  const hits = new Set();
  for (const patch of patches) {
    const text = String(patch ?? "");
    for (const token of tokens) {
      if (text.includes(token)) hits.add(token);
    }
  }
  return [...hits].sort();
}

export function deriveContractAction({ hard = [], semantic = [], semanticTokenHits = [] } = {}) {
  if (hard.length > 0) return "runtime-reaudit-required";
  if (semantic.length > 0 && semanticTokenHits.length > 0) return "targeted-semantic-review-required";
  if (semantic.length > 0) return "semantic-path-review-recommended";
  return "safe-advance-candidate";
}

export function runtimeCompatibilityFromDrift(device, drift = {}) {
  const invalidCapabilities = new Set();
  const tokenMap = {
    getStreams: ["invocation", "media-type", "settings"],
    PluginRuntimeResult: ["result-shape"],
    LocalScraperResult: ["result-shape"],
    proxyHeaders: ["headers", "referer", "origin"],
    httpHeaders: ["headers", "referer", "origin"],
    playbackUrl: ["media", "player"],
    videoUrl: ["media", "player"],
    SCRAPER_SETTINGS: ["settings"],
    quickjs: ["invocation", "javascript"],
    okhttp: ["headers", "cookies", "redirects", "transport"],
    ktor: ["headers", "cookies", "redirects", "transport"],
    exoplayer: ["media", "player"],
    media3: ["media", "player"],
    vlc: ["media", "player"],
  };

  for (const token of drift.semanticTokenHits ?? []) {
    for (const capability of tokenMap[token] ?? []) invalidCapabilities.add(capability);
  }
  if ((drift.hard ?? []).length > 0) {
    for (const capability of ["invocation", "result-shape", "settings", "transport"]) invalidCapabilities.add(capability);
  }

  return {
    device,
    action: deriveContractAction(drift),
    invalidCapabilities: [...invalidCapabilities].sort(),
  };
}

export function compareObservedHead(client, observedHead) {
  const accepted = client.accepted_ref;
  if (!accepted || !observedHead) return "unknown";
  return accepted === observedHead ? "current" : "drifted";
}

function matchesAnyPath(filename, paths) {
  return paths.some((path) => {
    if (!path) return false;
    if (path.endsWith("/")) return filename.startsWith(path);
    return filename === path || filename.startsWith(`${path}/`);
  });
}
