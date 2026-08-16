import assert from "node:assert/strict";
import { decideProviderState, lkgIsUsable } from "../src/decision-engine.mjs";

assert.equal(decideProviderState({ currentPlayableProofs: 2 }).state, "enabled-current-proof");
assert.equal(decideProviderState({ currentPlayableProofs: 0, failureClass: "search_gap" }).state, "repairable-disabled");
assert.equal(decideProviderState({ suspicious: true }).state, "hold-suspicious");
assert.equal(decideProviderState({ unsafe: true }).state, "quarantine");
assert.equal(decideProviderState({ confirmedIdentityMismatch: true }).state, "quarantine");

const now = "2026-08-16T18:00:00Z";
const recentLkg = { playable: true, validatedAt: "2026-08-16T12:00:00Z", maxAgeHours: 24 };
assert.equal(lkgIsUsable(recentLkg, now), true);
const grace = decideProviderState({ currentPlayableProofs: 0, lkg: recentLkg, now, failureClass: "transport_blocked" });
assert.equal(grace.state, "enabled-lkg-grace");
assert.equal(grace.publish, true);
assert.equal(grace.repair, true);

const oldLkg = { playable: true, validatedAt: "2026-08-10T12:00:00Z", maxAgeHours: 24 };
assert.equal(lkgIsUsable(oldLkg, now), false);
assert.equal(decideProviderState({ currentPlayableProofs: 0, lkg: oldLkg, now, failureClass: "transport_blocked" }).state, "repairable-disabled");

console.log("engine v2 decision engine tests passed");
