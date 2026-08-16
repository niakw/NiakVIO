import assert from "node:assert/strict";
import { buildDomainCandidates, chooseBestObservedDomain } from "../src/domain-discovery.mjs";

const candidates = buildDomainCandidates(
  { hosts: ["example.test", "github.com", "cdn.example.test"] },
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
assert.ok(candidates.some((c) => c.host === "lkg.example.test" && c.trust === 90));
assert.ok(candidates.some((c) => c.host === "example.test"));
assert.equal(candidates.some((c) => c.host === "github.com"), false);

const best = chooseBestObservedDomain([
  { host: "a", trust: 100, dns: { ok: true }, reachable: true, http: { status: 403 } },
  { host: "b", trust: 60, dns: { ok: true }, reachable: true, http: { status: 200 } },
  { host: "c", trust: 120, dns: { ok: false }, reachable: false, http: {} },
]);
assert.equal(best.host, "b");

const blockedOnly = chooseBestObservedDomain([
  { host: "a", trust: 80, dns: { ok: true }, reachable: true, http: { status: 403 } },
  { host: "b", trust: 100, dns: { ok: true }, reachable: true, http: { status: 403 } },
]);
assert.equal(blockedOnly.host, "b");

console.log("engine v2 domain discovery tests passed");
