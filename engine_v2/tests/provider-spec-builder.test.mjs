import assert from "node:assert/strict";
import { buildProviderSpec, buildProviderSpecs } from "../src/provider-spec-builder.mjs";

const inventoryProvider = {
  id: "example",
  names: ["Example"],
  supportedTypes: ["movie", "tv"],
  languages: ["fr"],
  formats: ["m3u8"],
  hasSettings: true,
  limited: false,
  supportsExternalPlayer: false,
  supportedPlatforms: [],
  disabledPlatforms: ["ios"],
  upstreamEnabledStates: { a: true, b: false },
  variants: [
    { source: { upstreamId: "a", repository: "x/a", ref: "1", manifestSha: "m1", filename: "providers/example.js" }, filename: "providers/example.js", version: "1.0.0", enabledUpstream: true, supportedTypes: ["movie", "tv"], languages: ["fr"], formats: ["m3u8"], disabledPlatforms: [] },
    { source: { upstreamId: "b", repository: "x/b", ref: "2", manifestSha: "m2", filename: "providers/example.js" }, filename: "providers/example.js", version: "1.1.0", enabledUpstream: false, supportedTypes: ["movie", "tv"], languages: ["fr"], formats: ["mp4"], disabledPlatforms: ["ios"] },
  ],
};
const knowledgeProvider = {
  id: "example",
  formats: ["m3u8", "mp4"],
  providerCandidateHosts: ["example.test"],
  playerHosts: ["player.test"],
  auxiliaryHosts: ["api.themoviedb.org"],
  domainRegistries: ["https://raw.githubusercontent.com/x/domains.json"],
  strategyKinds: ["hybrid"],
  observedStages: { episode: true, player: true, media: true },
  observedHeaders: { referer: true, origin: true, cookie: true, userAgent: true, authorization: false },
  routeHints: ["/api/search"],
  requiresSettings: true,
  state: "knowledge-seeded",
};
const spec = buildProviderSpec({
  inventoryProvider,
  knowledgeProvider,
  domainObservation: { selected: { url: "https://example.test/", status: 200 } },
  legacyHub: { hub: "https://hub.example.test/" },
});
assert.equal(spec.publishable, false);
assert.equal(spec.state, "spec-seeded-unverified");
assert.equal(spec.implementationCandidates.length, 2);
assert.ok(spec.requirements.includes("compare-upstream-implementations"));
assert.ok(spec.requirements.includes("cookie-aware-transport"));
assert.ok(spec.requirements.includes("dynamic-domain-registry"));
assert.equal(spec.discovery.observedDomain.status, 200);

const built = buildProviderSpecs({
  inventory: { providers: [inventoryProvider] },
  knowledge: { providers: [knowledgeProvider] },
  domains: { providers: [{ id: "example", selected: { url: "https://example.test/", status: 200 } }] },
  hubs: { providers: {} },
});
assert.equal(built.stats.specs, 1);
assert.equal(built.stats.errors, 0);
assert.equal(built.stats.duplicateImplementations, 1);
assert.equal(built.stats.requireCookies, 1);

console.log("engine v2 provider spec builder tests passed");
