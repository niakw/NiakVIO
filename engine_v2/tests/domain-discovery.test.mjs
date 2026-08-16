import assert from "node:assert/strict";
import {
  buildDomainCandidates,
  chooseBestObservedDomain,
  extractDomainCandidatesFromRegistry,
} from "../src/domain-discovery.mjs";

const candidates = buildDomainCandidates(
  { id: "example", names: ["Example"], providerCandidateHosts: ["example.test", "cdn.example.test"] },
  {
    hub: "https://hub.example.test/",
    direct: "https://example.test/",
    direct_candidates: ["https://mirror.example.test/"],
    sources: [{ type: "hub", url: "https://hub.example.test/", priority: 110 }],
  },
  { current: { url: "https://lkg.example.test/" } },
);
assert.equal(candidates[0].host, "hub.example.test");
assert.equal(candidates[0].trust, 110);
assert.equal(candidates[0].role, "hub");
assert.ok(candidates.some((c) => c.host === "lkg.example.test" && c.trust === 90 && c.role === "terminal"));
assert.ok(candidates.some((c) => c.host === "example.test" && c.role === "terminal"));

const best = chooseBestObservedDomain([
  { host: "hub", role: "hub", trust: 120, dns: { ok: true }, reachable: true, http: { status: 200 } },
  { host: "a", role: "terminal", trust: 100, dns: { ok: true }, reachable: true, http: { status: 403 } },
  { host: "b", role: "terminal", trust: 60, dns: { ok: true }, reachable: true, http: { status: 200 } },
  { host: "c", role: "terminal", trust: 120, dns: { ok: false }, reachable: false, http: {} },
]);
assert.equal(best.host, "b");
assert.notEqual(best.host, "hub");

const blockedOnly = chooseBestObservedDomain([
  { host: "hub", role: "hub", trust: 150, dns: { ok: true }, reachable: true, http: { status: 200 } },
  { host: "a", role: "terminal", trust: 80, dns: { ok: true }, reachable: true, http: { status: 403 } },
  { host: "b", role: "terminal", trust: 100, dns: { ok: true }, reachable: true, http: { status: 403 } },
]);
assert.equal(blockedOnly.host, "b");

const registry = extractDomainCandidatesFromRegistry({
  purstream: "purstream.club",
  purstream_api: "https://api.purstream.club/api/v1",
  unrelated: "https://totally-different.example/",
}, { id: "purstream", names: ["Purstream"] });
assert.ok(registry.some((row) => row.host === "purstream.club"));
assert.ok(registry.some((row) => row.host === "api.purstream.club"));
assert.equal(registry.some((row) => row.host === "totally-different.example"), false);

console.log("engine v2 domain discovery tests passed");
