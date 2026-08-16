#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { REPAIR_RECIPES } from "../src/repair-brain.mjs";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "../..");
const args = process.argv.slice(2);
const outIndex = args.indexOf("--output-dir");
const outputDir = path.resolve(outIndex >= 0 ? args[outIndex + 1] : path.join(root, "engine_v2/learning"));
fs.mkdirSync(outputDir, { recursive: true });

const overrides = readJson(path.join(root, "provider-overrides.json"), {});
const repair = readJson(path.join(root, "repair-report.json"), {});
const diagnostics = readJson(path.join(root, "diagnostics-report.json"), {});
const policy = readJson(path.join(root, "engine_v2/config/brain-policy.json"), {});
const skills = overrides.runtime_repair?.learned_skills ?? {};
const plans = repair.brain?.plans ?? {};

const counts = new Map();
for (const row of Object.values(plans)) {
  const failureClass = String(row?.failureClass ?? "unknown_failure");
  if (failureClass === "healthy") continue;
  counts.set(failureClass, (counts.get(failureClass) ?? 0) + 1);
}

const trustedByFailure = new Map();
for (const skill of Object.values(skills)) {
  if (!skill || skill.autoApply !== true) continue;
  const key = String(skill.failureClass ?? skill.failure_class ?? "unknown_failure");
  trustedByFailure.set(key, (trustedByFailure.get(key) ?? 0) + 1);
}

const proposals = [];
for (const [failureClass, count] of [...counts.entries()].sort((a, b) => b[1] - a[1])) {
  const recipes = REPAIR_RECIPES[failureClass] ?? REPAIR_RECIPES.unknown_failure;
  if (count >= 2 && (trustedByFailure.get(failureClass) ?? 0) === 0) {
    proposals.push({
      type: "skill_candidate",
      priority: count >= 5 ? "high" : "medium",
      failureClass,
      evidenceCount: count,
      proposedSkill: {
        id: `learning-${failureClass}`,
        compose: recipes.map((row) => row.id).slice(0, 3),
        capabilities: [...new Set(recipes.flatMap((row) => row.capabilities ?? []))],
        execution: "sandbox_only_until_cross-provider-proof",
      },
      reason: "Repeated unresolved failure class without a trusted reusable skill.",
    });
  }
}

const unknown = counts.get("unknown_failure") ?? 0;
if (unknown >= 3) {
  proposals.push({
    type: "instrumentation_proposal",
    priority: "high",
    target: "evidence pipeline",
    reason: `${unknown} unresolved observations still lack a causal stage classification.`,
    proposal: "Add stage evidence before adding another repair mutation; never use a generic provider fallback as diagnosis.",
  });
}

const drift = counts.get("runtime_contract_drift") ?? 0;
if (drift > 0) {
  proposals.push({
    type: "core_proposal",
    priority: "high",
    target: "runtime contract adapter",
    reason: `${drift} runtime-contract drift observation(s).`,
    proposal: "Re-audit official Nuvio device contracts and propose a core adapter change; production core remains immutable until reviewed.",
  });
}

const payload = {
  schemaVersion: 1,
  generatedAt: new Date().toISOString(),
  brain: policy.identity ?? { name: "NiakVIO Brain" },
  mode: "learning_lab",
  publicationAllowed: false,
  productionWritesAllowed: false,
  proposals,
  learnedSkillCount: Object.keys(skills).length,
  unresolvedFailureCounts: Object.fromEntries(counts),
  diagnosticsAvailable: Boolean(Object.keys(diagnostics).length),
  privacy: "No raw URLs, tokens, header values, private notes or spreadsheet text are copied into learning proposals.",
};

fs.writeFileSync(path.join(outputDir, "latest.json"), JSON.stringify(payload, null, 2) + "\n");
fs.writeFileSync(path.join(outputDir, "latest.md"), renderMarkdown(payload));
console.log(`FIELD_BRAIN_LEARNING proposals=${proposals.length} skills=${payload.learnedSkillCount}`);
process.exitCode = 0;

function readJson(file, fallback) {
  try { return JSON.parse(fs.readFileSync(file, "utf8")); } catch { return fallback; }
}
function renderMarkdown(data) {
  const lines = [
    `# ${data.brain?.name ?? "NiakVIO Brain"} — Learning Lab`, "",
    "Sandbox R&D only. Nothing in this report is applied to production automatically.", "",
    `Generated: ${data.generatedAt}`, "",
    `Learned skills observed: **${data.learnedSkillCount}**`, "",
    "## Proposals", "",
  ];
  if (!data.proposals.length) lines.push("No new proposal this run.");
  data.proposals.forEach((proposal, index) => {
    lines.push(`### ${index + 1}. ${proposal.type} — ${proposal.priority}`);
    lines.push("");
    if (proposal.failureClass) lines.push(`Failure class: \`${proposal.failureClass}\``);
    lines.push(proposal.reason ?? "");
    if (proposal.proposal) lines.push("", proposal.proposal);
    if (proposal.proposedSkill) lines.push("", `Candidate composition: \`${proposal.proposedSkill.compose.join(" → ")}\``);
    lines.push("");
  });
  lines.push("## Privacy", "", data.privacy, "");
  return lines.join("\n");
}
