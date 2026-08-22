#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-only
/**
 * Conservative provider-bundle purification.
 *
 * Phase 1 intentionally does NOT mangle identifiers. Provider runtimes can use
 * eval/function names/source inspection, so the first optimization layer focuses
 * on deterministic formatting + a deliberately small set of safe compression
 * transforms. Exact runtime/deep/native proof remains authoritative afterwards.
 */
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { minify } from "terser";

const EXPECTED_TERSER_VERSION = "5.50.0";

function arg(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : null;
}

function riskFlags(code) {
  const flags = [];
  if (/\beval\s*\(/.test(code)) flags.push("dynamic_eval");
  if (/\bnew\s+Function\s*\(|\bFunction\s*\(/.test(code)) flags.push("dynamic_function_constructor");
  if (/\.toString\s*\(\s*\)/.test(code) && /\bfunction\b|=>/.test(code)) flags.push("function_source_introspection");
  if (/\bsourceURL\b|\bsourceMappingURL\b/.test(code)) flags.push("source_directive");
  return flags;
}

async function terserVersion() {
  const packagePath = new URL("../../node_modules/terser/package.json", import.meta.url);
  try {
    const parsed = JSON.parse(await fs.readFile(packagePath, "utf8"));
    return String(parsed.version || "");
  } catch {
    try {
      const resolved = await import("terser/package.json", { with: { type: "json" } });
      return String(resolved.default?.version || "");
    } catch {
      return "unknown";
    }
  }
}

async function main() {
  const input = arg("--input");
  const output = arg("--output");
  const forceFormatOnly = process.argv.includes("--format-only");
  if (!input || !output) throw new Error("usage: purify-provider.mjs --input <file.js> --output <file.js> [--format-only]");

  const code = await fs.readFile(input, "utf8");
  const flags = riskFlags(code);
  const version = await terserVersion();
  if (version !== EXPECTED_TERSER_VERSION) {
    throw new Error(`Terser version mismatch: expected ${EXPECTED_TERSER_VERSION}, got ${version}`);
  }

  const risky = flags.includes("dynamic_eval") || flags.includes("dynamic_function_constructor") || flags.includes("function_source_introspection");
  const compress = (forceFormatOnly || risky) ? false : {
    defaults: false,
    booleans: true,
    comparisons: true,
    conditionals: true,
    dead_code: true,
    if_return: true,
    join_vars: true,
    loops: true,
    collapse_vars: false,
    evaluate: false,
    hoist_funs: false,
    hoist_props: false,
    hoist_vars: false,
    inline: false,
    properties: false,
    reduce_funcs: false,
    reduce_vars: false,
    sequences: false,
    side_effects: false,
    switches: false,
    typeofs: false,
    unsafe: false,
  };

  const result = await minify(code, {
    ecma: 2022,
    module: false,
    toplevel: false,
    compress,
    mangle: false,
    keep_classnames: true,
    keep_fnames: true,
    format: {
      beautify: false,
      braces: false,
      comments: /(?:@license|@preserve|NUVIO_|^!)/,
      semicolons: true,
    },
  });
  if (!result.code) throw new Error("Terser returned no code");

  const purified = `${result.code}\n`;
  await fs.mkdir(path.dirname(path.resolve(output)), { recursive: true });
  await fs.writeFile(output, purified, "utf8");

  const mode = forceFormatOnly ? "format-only" : (risky ? "risk-format-only" : "conservative-compression");
  const payload = {
    schemaVersion: 2,
    tool: "terser",
    toolVersion: version,
    phase: "provider-purification-v1",
    mode,
    mangle: false,
    conservativeCompression: mode === "conservative-compression",
    riskFlags: flags,
    bytesBefore: Buffer.byteLength(code),
    bytesAfter: Buffer.byteLength(purified),
  };
  process.stdout.write(`NIAKVIO_PURIFICATION_RESULT=${JSON.stringify(payload)}\n`);
}

main().catch((error) => {
  process.stderr.write(`provider purification failed: ${error?.stack || error}\n`);
  process.exitCode = 1;
});