import assert from "node:assert/strict";
import {
  addEvidenceError,
  aggregateProviderEvidence,
  makeEvidenceKey,
  newEvidenceRecord,
  recordStage,
  summarizeEvidence,
} from "../src/evidence.mjs";

const base = {
  providerId: "purstream",
  fixtureId: "breaking-bad-s01e01",
  mediaType: "tv",
  language: "fr",
  device: "tv",
  clientRef: "abc123",
};

assert.equal(
  makeEvidenceKey(base),
  "purstream::breaking-bad-s01e01::tv::fr::tv::abc123",
);

const record = newEvidenceRecord(base);
record.invoked = true;
recordStage(record, "dns", { ok: true });
recordStage(record, "homepage", { status: 200 });
recordStage(record, "search", { status: 200, matches: 1 });
recordStage(record, "identity", { matched: true });
recordStage(record, "detail", { found: true });
recordStage(record, "episode", { found: true, season: 1, episode: 1 });
recordStage(record, "player", { found: true });
recordStage(record, "media", { found: true, status: 206, playable: true });
recordStage(record, "runtime", { accepted: true });
record.playableStreams = 1;

const summary = summarizeEvidence(record);
assert.equal(summary.complete, true);
assert.equal(summary.playableStreams, 1);
assert.equal(summary.firstMissingStage, null);

const desktop = newEvidenceRecord({ ...base, device: "desktop" });
desktop.invoked = true;
recordStage(desktop, "dns", { ok: true });
addEvidenceError(desktop, "native runtime returned zero streams");

const aggregate = aggregateProviderEvidence([record, desktop]);
assert.equal(aggregate.proofCount, 2);
assert.equal(aggregate.playableProofs, 1);
assert.equal(aggregate.byDevice.tv.playable, 1);
assert.equal(aggregate.byDevice.desktop.playable, 0);

console.log("engine v2 evidence matrix tests passed");
