export function analyzeProviderCode(code = "") {
  const text = String(code);
  const urls = extractUrls(text);
  const hosts = unique(urls.map(hostFromUrl).filter(Boolean));
  const routeHints = extractRouteHints(text);
  const requestMethods = new Set();
  if (/\bfetch\s*\(/.test(text)) requestMethods.add("GET/default-fetch");
  if (/\baxios\.get\s*\(/i.test(text)) requestMethods.add("GET/axios");
  if (/\baxios\.post\s*\(/i.test(text)) requestMethods.add("POST/axios");
  if (/method\s*:\s*["'`]POST["'`]/i.test(text)) requestMethods.add("POST/fetch");
  if (/method\s*:\s*["'`]HEAD["'`]/i.test(text)) requestMethods.add("HEAD/fetch");

  const headers = detectTokens(text, {
    referer: /\breferer\b/i,
    origin: /\borigin\b/i,
    cookie: /\bcookie\b/i,
    userAgent: /user-agent|userAgent/i,
    authorization: /authorization|bearer\s+/i,
    xRequestedWith: /x-requested-with/i,
  });
  const libraries = detectTokens(text, {
    fetch: /\bfetch\s*\(/,
    axios: /\baxios\b/i,
    cheerio: /\bcheerio\b/i,
    cryptoJs: /\bCryptoJS\b/,
    wasm: /\bWebAssembly\b|\.wasm\b/,
    domParser: /DOMParser|querySelector/i,
  });
  const settings = {
    readsScraperSettings: /SCRAPER_SETTINGS|scraperSettings|settings\s*\[/i.test(text),
    exposesOnSettings: /\bonSettings\b/.test(text),
  };
  const mediaFormats = unique([
    /\.m3u8\b/i.test(text) ? "m3u8" : null,
    /\.mpd\b/i.test(text) ? "mpd" : null,
    /\.mp4\b/i.test(text) ? "mp4" : null,
    /\.mkv\b/i.test(text) ? "mkv" : null,
  ].filter(Boolean));
  const stages = detectTokens(text, {
    tmdb: /\btmdb/i,
    search: /\bsearch\b|\/search[/?]/i,
    detail: /\bdetail\b|\bwatch\b|\bslug\b/i,
    episode: /\bseason\b|\bepisode\b/i,
    player: /\biframe\b|\bembed\b|\bplayer\b/i,
    media: /m3u8|\.mp4|\.mpd|playlist|manifest/i,
  });

  return {
    byteLength: Buffer.byteLength(text, "utf8"),
    lineCount: text ? text.split(/\r?\n/).length : 0,
    exports: {
      getStreams: /\bgetStreams\b/.test(text),
      moduleExports: /module\.exports/.test(text),
      onSettings: settings.exposesOnSettings,
    },
    urls,
    hosts,
    routeHints,
    requestMethods: [...requestMethods],
    headers,
    libraries,
    settings,
    mediaFormats,
    stages,
    strategyKind: inferStrategyKind({ text, stages, libraries, urls }),
    typeLogic: {
      mediaType: /\bmediaType\b/.test(text),
      season: /\bseason\b/.test(text),
      episode: /\bepisode\b/.test(text),
      explicitTv: /["'`]tv["'`]/.test(text),
      explicitMovie: /["'`]movie["'`]/.test(text),
      explicitAnime: /["'`]anime["'`]/.test(text),
    },
  };
}

export function mergeProviderKnowledge(provider, analyzedVariants) {
  return {
    id: provider.id,
    supportedTypes: provider.supportedTypes,
    languages: provider.languages,
    formats: unique([...provider.formats, ...analyzedVariants.flatMap((v) => v.analysis.mediaFormats)]),
    hosts: unique(analyzedVariants.flatMap((v) => v.analysis.hosts)),
    routeHints: unique(analyzedVariants.flatMap((v) => v.analysis.routeHints)),
    strategyKinds: unique(analyzedVariants.map((v) => v.analysis.strategyKind)),
    requiresSettings: provider.hasSettings || analyzedVariants.some((v) => v.analysis.settings.readsScraperSettings),
    observedHeaders: mergeBooleanMaps(analyzedVariants.map((v) => v.analysis.headers)),
    observedStages: mergeBooleanMaps(analyzedVariants.map((v) => v.analysis.stages)),
    variants: analyzedVariants,
    state: analyzedVariants.some((v) => v.error) ? "knowledge-partial" : "knowledge-seeded",
  };
}

function extractUrls(text) {
  const matches = text.match(/https?:\/\/[^\s"'`<>\\)\]}]+/gi) ?? [];
  return unique(matches.map((value) => value.replace(/[.,;:]+$/, ""))).slice(0, 200);
}

function extractRouteHints(text) {
  const literals = [];
  const re = /["'`]([^"'`\n]{1,180})["'`]/g;
  let match;
  while ((match = re.exec(text))) {
    const value = match[1];
    if (/\/(api|ajax|search|embed|player|watch|episode|episodes|movie|movies|series|tv|stream|source|sources|server|servers)(\/|\?|$)/i.test(value)) {
      literals.push(value);
    }
  }
  return unique(literals).slice(0, 100);
}

function hostFromUrl(value) {
  try { return new URL(value).hostname.toLowerCase(); } catch { return null; }
}

function detectTokens(text, map) {
  return Object.fromEntries(Object.entries(map).map(([name, regex]) => [name, regex.test(text)]));
}

function inferStrategyKind({ text, stages, libraries, urls }) {
  const apiSignals = /\/api\/|graphql|application\/json|\.json\b|axios/i.test(text);
  const htmlSignals = libraries.cheerio || /querySelector|\.html\(\)|\.text\(\)/i.test(text);
  const playerSignals = stages.player;
  const directMedia = urls.some((url) => /\.(m3u8|mpd|mp4|mkv)(\?|$)/i.test(url));
  if (apiSignals && (htmlSignals || playerSignals)) return "hybrid";
  if (apiSignals) return "api";
  if (htmlSignals || playerSignals) return "html/embed";
  if (directMedia) return "direct-media";
  return "unknown";
}

function mergeBooleanMaps(maps) {
  const keys = unique(maps.flatMap((map) => Object.keys(map ?? {})));
  return Object.fromEntries(keys.map((key) => [key, maps.some((map) => map?.[key] === true)]));
}

function unique(values) {
  return [...new Set(values)];
}
