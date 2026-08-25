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
const GENERATED_MARKER = String.raw`\/\*\s*(NUVIO_[^*\r\n]+?)\s*\*\/`;
const GENERATED_SUFFIX = String.raw`(?=(?:[;!~+\-]\s*)?(?:\(\s*)?(?:async\s+)?function\b|(?:[;!~+\-]\s*)?\(\s*(?:\([^)]*\)|[$\w]+)\s*=>)`;

export function canonicalizeRetainedCoreBoundary(code) {
  const first = code.indexOf(RETAINED_AUDIO_MARKER);
  if (first < 0) return code;
  if (code.indexOf(RETAINED_AUDIO_MARKER, first + RETAINED_AUDIO_MARKER.length) >= 0) {
    throw new Error("duplicate retained HLS master audio marker");
  }

  const left = code.slice(0, first).replace(/[ \t\r\n]+$/, "");
  const right = code.slice(first + RETAINED_AUDIO_MARKER.length).replace(/^[ \t\r\n]+/, "");
  const prefix = left ? `${left}\n` : "";
  const suffix = right ? `\n${right}` : "";
  return `${prefix}${RETAINED_AUDIO_MARKER}${suffix}`;
}

export function canonicalizeGeneratedMarkerBoundaries(code) {
  // Terser may attach a preserved NUVIO marker before `);`, between `)` and `;`,
  // or after `);`; it may also vary whitespace and the following IIFE syntax.
  // Collapse every owned representation to one byte-stable boundary. Leading
  // whitespace belongs to this generated boundary too: leaving it behind caused
  // AnimePahe/AnimeZey to grow one newline per rebuild.
  const patterns = [
    new RegExp(String.raw`[ \t\r\n]*${GENERATED_MARKER}[ \t\r\n]*\);[ \t\r\n]*${GENERATED_SUFFIX}`, "g"),
    new RegExp(String.raw`\)[ \t\r\n]*${GENERATED_MARKER}[ \t\r\n]*;[ \t\r\n]*${GENERATED_SUFFIX}`, "g"),
    new RegExp(String.raw`\);[ \t\r\n]*${GENERATED_MARKER}[ \t\r\n]*${GENERATED_SUFFIX}`, "g"),
  ];
  let moved = 0;
  let output = code;
  for (const pattern of patterns) {
    output = output.replace(pattern, (match, rawMarker) => {
      const replacement = `);\n/* ${String(rawMarker).trim()} */\n`;
      if (match !== replacement) moved += 1;
      return replacement;
    });
  }
  return { code: output, moved };
}

export function canonicalizeOwnedBoundaries(code) {
  const audio = canonicalizeRetainedCoreBoundary(code);
  const generated = canonicalizeGeneratedMarkerBoundaries(audio);
  return {
    code: generated.code,
    retainedAudioChanged: audio !== code,
    floatedMarkerCount: generated.moved,
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
