#!/usr/bin/env python3
"""Candidate-only V31: retain an already-fetched HLS receipt across deduplication.

V30 can fetch the signed HLS root and attach a bounded in-memory Core receipt,
but the crawler first emits an unverified URL from the player HTML. The common
playback-identity deduper keeps the first row, discarding the later proven row,
so Core refetches the same root and may receive 403.

V31 is intentionally NOT published. Apply only to exact Brain-selected,
source-attested, isolated ProviderBase experiment bytes; keep downstream Core
playlist/segment validation and private-proof cleanup unchanged.
"""
from __future__ import annotations

from .native_hls_root_receipt_v1 import MARKER as V30_MARKER
from .native_hls_root_receipt_v1 import apply as apply_v30

MARKER = "NIAKVIO_PROVIDER_NATIVE_HLS_RECEIPT_DEDUPE_V31"

OLD = """function _dedupeStreamRows(rows) {
  const out = [];
  const seen = new Set();
  for (const row of rows || []) {
    const key = _streamPlaybackKey(row);
    if (!key || seen.has(key)) continue;
    seen.add(key);
    out.push(row);
    if (out.length >= 40) break;
  }
  return out;
}
"""

NEW = r"""/* NIAKVIO_PROVIDER_NATIVE_HLS_RECEIPT_DEDUPE_V31 */
function _dedupeStreamRows(rows) {
  const out = [];
  const seen = new Map();
  // This is a *transient* network witness, never playback authority. Exact
  // URL and playback-header identity remain required for safe deduplication.
  function validReceipt(row) {
    const proof = row && row.__nuvioCoreMediaProofV1;
    if (!proof || typeof proof !== "object" ||
        proof.kind !== "hls" || proof.url !== row.url ||
        typeof proof.body !== "string" || proof.body.length > 131072 ||
        !/^#EXTM3U(?:\r?\n|$)/.test(proof.body) ||
        !/#EXT-(?:X-STREAM-INF|X-TARGETDURATION|INF)\b/.test(proof.body)) return null;
    return proof;
  }
  for (const row of rows || []) {
    const key = _streamPlaybackKey(row);
    if (!key) continue;
    if (seen.has(key)) {
      const index = seen.get(key);
      const receipt = validReceipt(row);
      // Keep metadata/reader identity of the first row, upgrade only the
      // same-URL, same-header root witness. Do not merge two language variants
      // or leak a signed playlist into final provider output.
      if (receipt && !validReceipt(out[index])) {
        out[index] = Object.assign({}, out[index],
          {__nuvioCoreMediaProofV1: receipt});
      }
      continue;
    }
    seen.set(key, out.length);
    out.push(row);
    if (out.length >= 40) break;
  }
  return out;
}
"""


def apply(base: bytes) -> bytes:
    """Build a separate V31 workspace-only candidate, including V30 capture."""
    source = base.decode("utf-8", errors="strict")
    if MARKER in source or V30_MARKER in source:
        raise ValueError("V31 expects an unmodified original common ProviderBase")
    first = apply_v30(base).decode("utf-8", errors="strict")
    if first.count(OLD) != 1:
        raise ValueError("ProviderBase V31 dedupe anchor drift")
    result = first.replace(OLD, NEW, 1).encode("utf-8")
    validate(result)
    return result


def validate(data: bytes) -> None:
    source = data.decode("utf-8", errors="strict")
    if source.count(MARKER) != 1 or source.count(V30_MARKER) != 1 or OLD in source:
        raise ValueError("V31 receipt candidate was not built from exact V30 + dedupe")
    required = (
        "seen.has(key)", "seen.get(key)", "proof.url !== row.url",
        "__nuvioCoreMediaProofV1: receipt", "proof.body.length > 131072",
        "validReceipt(out[index])", "out[index] = Object.assign(",
    )
    for value in required:
        if value not in source:
            raise ValueError("V31 fail-closed dedupe guard absent: " + value)
