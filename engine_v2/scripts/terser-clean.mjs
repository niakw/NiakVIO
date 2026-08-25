#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-only
/**
 * Single NiakVIO gateway for Terser output.
 *
 * Every Terser pass must flow through minifyAndClean(). That makes post-minify
 * canonicalization part of the minification contract instead of an optional
 * call-site detail. The cleanup owns only NiakVIO-generated comment boundaries
 * and terminal whitespace; provider JavaScript semantics stay untouched.
 */
import { minify } from "terser";

export const RETAINED_AUDIO_MARKER = "/* NUVIO_HLS_MASTER_AUDIO_PRESERVER_V1 */";

export function canonicalizeRetainedCoreBoundary(code) {
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

export function canonicalizeFloatedGeneratedMarkers(code) {
  // Terser can preserve one of our comments while attaching it to the final AST
  // node of the provider export expression. Two equivalent shapes are observed:
  // the marker may still sit before the terminal `);`, or Terser may already have
  // attached it immediately after that punctuation. Normalize both to the same
  // owned boundary before choosing bytes, otherwise the first pass can publish
  // `);/* NUVIO_... */(function` while the contract expects a stable line boundary.
  let moved = 0;
  const canonical = (rawMarker) => `);\n/* ${String(rawMarker).trim()} */\n(function`;

  const settledPattern = /\);[ \t\r\n]*\/\*\s*(NUVIO_[^*\r\n]+?)\s*\*\/[ \t\r\n]*\(function\b/g;
  let output = code.replace(settledPattern, (match, rawMarker) => {
    const replacement = canonical(rawMarker);
    if (match !== replacement) moved += 1;
    return replacement;
  });

  const floatedPattern = /\/\*\s*(NUVIO_[^*\r\n]+?)\s*\*\/[ \t\r\n]*\);[ \t\r\n]*\(function\b/g;
  output = output.replace(floatedPattern, (_match, rawMarker) => {
    moved += 1;
    return canonical(rawMarker);
  });
  return { code: output, moved };
}

export function canonicalizeOwnedBoundaries(code) {
  const audio = canonicalizeRetainedCoreBoundary(code);
  const floated = canonicalizeFloatedGeneratedMarkers(audio);
  return {
    code: floated.code,
    retainedAudioChanged: audio !== code,
    floatedMarkerCount: floated.moved,
  };
}

export function withTerminalNewline(code) {
  return code.endsWith("\n") ? code : `${code}\n`;
}

export function cleanTerserOutput(code) {
  const boundary = canonicalizeOwnedBoundaries(code);
  return {
    code: withTerminalNewline(boundary.code),
    boundary,
  };
}

export async function minifyAndClean(code, options) {
  const result = await minify(code, options);
  if (!result.code) throw new Error("Terser returned no code");
  const cleaned = cleanTerserOutput(result.code);
  return {
    result: { ...result, code: cleaned.code },
    boundary: cleaned.boundary,
  };
}
