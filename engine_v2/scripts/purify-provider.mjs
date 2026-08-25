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
const RETAINED_AUDIO_MARKER = "/* NUVIO_HLS_MASTER_AUDIO_PRESERVER_V1 */";

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

function canonicalizeRetainedCoreBoundary(code) {
  const first = code.indexOf(RETAINED_AUDIO_MARKER);
  if (first < 0) return code;
  if (code.indexOf(RETAINED_AUDIO_MARKER, first + RETAINED_AUDIO_MARKER.length) >= 0) {
    throw new Error("duplicate retained HLS master audio marker");
  }

  // The audio marker records an in-place provider rewrite and can therefore
  // remain immediately before the generated Core start boundary when the rest
  // of the Core tail is stripped/rebuilt. Own only surrounding whitespace: one
  // newline before and one after the marker, with all JavaScript bytes untouched.
  const left = code.slice(0, first).replace(/[ \t\r\n]+$/, "");
  const right = code.slice(first + RETAINED_AUDIO_MARKER.length).replace(/^[ \t\r\n]+/, "");
  const prefix = left ? `${left}\n` : "";
  const suffix = right ? `\n${right}` : "";
  return `${prefix}${RETAINED_AUDIO_MARKER}${suffix}`;
}

function withTerminalNewline(code) {
  return code.endsWith("\n") ? code : `${code}\n`;
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

  const source = await fs.readFile(input, "utf8");
  const code = canonicalizeRetainedCoreBoundary(source);
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

  const canonicalSource = withTerminalNewline(code);
  const terserCandidate = withTerminalNewline(canonicalizeRetainedCoreBoundary(result.code));
  // Boundary canonicalization is an owned metadata normalization, not an
  // optimization. Never discard it merely because an already-compact provider
  // gives Terser no size win. If Terser is not strictly smaller, publish the
  // canonical source bytes; the second pass then proves the same fixed point.
  const useCanonicalSource = Buffer.byteLength(terserCandidate) >= Buffer.byteLength(canonicalSource);
  const purified = useCanonicalSource ? canonicalSource : terserCandidate;
  await fs.mkdir(path.dirname(path.resolve(output)), { recursive: true });
  await fs.writeFile(output, purified, "utf8");

  const baseMode = forceFormatOnly ? "format-only" : (risky ? "risk-format-only" : "conservative-compression");
  const mode = useCanonicalSource && source !== canonicalSource ? "boundary-canonicalization" : baseMode;
  const payload = {
    schemaVersion: 2,
    tool: "terser",
    toolVersion: version,
    phase: "provider-purification-v1",
    mode,
    mangle: false,
    conservativeCompression: !useCanonicalSource && baseMode === "conservative-compression",
    riskFlags: flags,
    bytesBefore: Buffer.byteLength(source),
    bytesAfter: Buffer.byteLength(purified),
    retainedAudioBoundaryCanonicalized: source !== canonicalSource && source.includes(RETAINED_AUDIO_MARKER),
  };
  process.stdout.write(`NIAKVIO_PURIFICATION_RESULT=${JSON.stringify(payload)}\n`);
}

main().catch((error) => {
  process.stderr.write(`provider purification failed: ${error?.stack || error}\n`);
  process.exitCode = 1;
});
