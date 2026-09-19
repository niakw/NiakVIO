#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { classifyChangedPaths, classifySemanticTokens, deriveContractAction } from "../src/contract-watcher.mjs";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const configPath = path.join(root, "config", "nuvio-clients.json");
const outputArg = argValue("--output") ?? path.join(root, "reports", "nuvio-contract-drift.json");
const enforce = process.argv.includes("--enforce");
const config = JSON.parse(await fs.readFile(configPath, "utf8"));
const report = {
  schema_version: 1,
  generated_at: new Date().toISOString(),
  mode: enforce ? "enforce-hard-contract-only" : "report-only",
  clients: {},
};

for (const [id, client] of Object.entries(config.clients)) {
  try {
    const headCommit = await githubJson(`/repos/${client.repository}/commits/${encodeURIComponent(client.branch)}`);
    const head = headCommit.sha;
    const result = {
      repository: client.repository,
      branch: client.branch,
      audited_ref: client.audited_ref,
      accepted_ref: client.accepted_ref,
      configured_observed_head: client.observed_head,
      current_head: head,
      status: head === client.accepted_ref ? "current" : "ahead-of-accepted",
      hard_changed_files: [],
      semantic_changed_files: [],
      semantic_token_hits: [],
      unrelated_changed_files: [],
      action: "none",
    };

    if (head !== client.accepted_ref) {
      const compare = await githubJson(`/repos/${client.repository}/compare/${client.accepted_ref}...${head}`);
      const files = compare.files ?? [];
      const classified = classifyChangedPaths(client, files);
      const semanticPatches = files
        .filter((file) => classified.semantic.includes(file.filename) || classified.hard.includes(file.filename))
        .map((file) => file.patch ?? "");
      const tokenHits = classifySemanticTokens(semanticPatches, config.semantic_tokens ?? []);
      result.status = compare.status ?? result.status;
      result.ahead_by = compare.ahead_by ?? null;
      result.hard_changed_files = classified.hard;
      result.semantic_changed_files = classified.semantic;
      result.unrelated_changed_files = classified.unrelated;
      result.semantic_token_hits = tokenHits;
      result.action = deriveContractAction({ ...classified, semanticTokenHits: tokenHits });
    }

    report.clients[id] = result;
  } catch (error) {
    report.clients[id] = {
      repository: client.repository,
      branch: client.branch,
      status: "watch-error",
      action: "manual-review-recommended",
      error: String(error?.message ?? error),
    };
  }
}

await fs.mkdir(path.dirname(outputArg), { recursive: true });
await fs.writeFile(outputArg, `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report, null, 2));

if (enforce) {
  const hardDrift = Object.values(report.clients).some((client) => client.hard_changed_files?.length > 0);
  if (hardDrift) process.exitCode = 2;
}

async function githubJson(apiPath) {
  const headers = {
    Accept: "application/vnd.github+json",
    "User-Agent": "NiakVIO-Provider-Engine-V2",
    "X-GitHub-Api-Version": "2022-11-28",
  };
  if (process.env.GITHUB_TOKEN) headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  const response = await fetch(`https://api.github.com${apiPath}`, { headers });
  if (!response.ok) throw new Error(`GitHub ${response.status} for ${apiPath}: ${await response.text()}`);
  return response.json();
}

function argValue(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : null;
}
