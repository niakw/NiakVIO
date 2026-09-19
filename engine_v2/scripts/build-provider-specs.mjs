#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { buildProviderSpecs } from "../src/provider-spec-builder.mjs";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const repoRoot = path.resolve(root, "..");
const inventory = await readJson(argValue("--inventory") ?? path.join(root, "reports", "provider-upstream-inventory.json"));
const knowledge = await readJson(argValue("--knowledge") ?? path.join(root, "reports", "provider-knowledge-seed.json"));
const domains = await readJson(argValue("--domains") ?? path.join(root, "reports", "provider-domain-observations.json"), { providers: [] });
const hubs = await readJson(path.join(repoRoot, "provider-hubs.json"), { providers: {} });
const output = argValue("--output") ?? path.join(root, "reports", "provider-specs-v2.json");

const built = buildProviderSpecs({ inventory, knowledge, domains, hubs });
const report = {
  schema_version: 1,
  generated_at: new Date().toISOString(),
  policy: "specs are knowledge artifacts only; publishable remains false until runtime evidence passes",
  ...built,
};
await fs.mkdir(path.dirname(output), { recursive: true });
await fs.writeFile(output, `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report.stats, null, 2));
if (report.errors.length) process.exitCode = 2;

async function readJson(file, fallback = null) {
  try { return JSON.parse(await fs.readFile(file, "utf8")); }
  catch (error) {
    if (fallback != null) return fallback;
    throw error;
  }
}

function argValue(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : null;
}
