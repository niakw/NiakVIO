#!/usr/bin/env python3
"""V21: shared obfuscated-HLS player decoding + bounded provider-plan trace.

Live V20.5.1 proof exposed two independent generic gaps:
- proof-backed player embeds can encode the real HLS URL as base64 + reverse +
  hostname-derived XOR while exposing a fake /troll/master.m3u8 decoy;
- the provider-value diagnostic retained only the final state, hiding why a
  materialized plan never reached provider network.

V21 adds a content-shape player decoder to the shared ProviderBase crawler and a
bounded, sanitized lifecycle history for provider-value execution. It contains no
provider id, provider host, fixture title, token, response body, cookie or secret.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import upgrade_provider_response_value_correlation_v20_5_1 as v2051  # noqa: E402

BASE = v2051.BASE
MARKER = "NIAKVIO_PROVIDER_SHARED_PLAYER_TRACE_V21"
TRACE_MARKER = "NIAKVIO_PROVIDER_VALUE_TRACE_HISTORY_V21"
PLAYER_MARKER = "NIAKVIO_PROVIDER_OBFUSCATED_HLS_PLAYER_V21"

patch_worker = v2051.patch_worker
patch_proof = v2051.patch_proof
patch_recovery = v2051.patch_recovery
patch_materializer = v2051.patch_materializer
validate_worker = v2051.validate_worker
validate_proof = v2051.validate_proof
validate_recovery = v2051.validate_recovery
validate_materializer = v2051.validate_materializer


def _once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_base() -> bool:
    v2051.patch_base()
    text = BASE.read_text(encoding="utf-8")
    if MARKER in text:
        validate_base(text)
        return False

    old_trace = r'''function _spv184Trace(stage, mediaType, providerId, stepIndex, route) {
  try {
    globalThis.__nuvioProviderValueTraceV18 = {
      stage: _text(stage).slice(0, 64),
      lane: _text(mediaType).slice(0, 32),
      providerId: _text(providerId).slice(0, 160),
      stepIndex: Number.isFinite(Number(stepIndex)) ? Number(stepIndex) : -1,
      route: _text(route).slice(0, 240)
    };
  } catch (_) {}
}
'''
    new_trace = r'''/* NIAKVIO_PROVIDER_VALUE_TRACE_HISTORY_V21 */
function _spv184Trace(stage, mediaType, providerId, stepIndex, route) {
  try {
    const row = {
      stage: _text(stage).slice(0, 64),
      lane: _text(mediaType).slice(0, 32),
      providerId: _text(providerId).slice(0, 160),
      stepIndex: Number.isFinite(Number(stepIndex)) ? Number(stepIndex) : -1,
      route: _text(route).slice(0, 240)
    };
    globalThis.__nuvioProviderValueTraceV18 = row;
    const history = Array.isArray(globalThis.__nuvioProviderValueTraceHistoryV21)
      ? globalThis.__nuvioProviderValueTraceHistoryV21 : [];
    history.push(row);
    while (history.length > 48) history.shift();
    globalThis.__nuvioProviderValueTraceHistoryV21 = history;
  } catch (_) {}
}
'''
    text = _once(text, old_trace, new_trace, "v21-bounded-plan-trace")

    crawler_anchor = "async function _crawlDirectMedia(seedUrls, referer, maxDepth) {\n"
    helper = r'''/* NIAKVIO_PROVIDER_SHARED_PLAYER_TRACE_V21 */
/* NIAKVIO_PROVIDER_OBFUSCATED_HLS_PLAYER_V21 */
function _spv21DecodedObfuscatedHls(html, pageUrl) {
  const source = _text(html).slice(0, 1048576);
  if (!source || !/^https?:\/\//i.test(_text(pageUrl))) return "";
  let hostname = "";
  try { hostname = new URL(pageUrl).hostname || ""; } catch (_) { return ""; }
  let videoUrl = "";

  // Current family: encoded string is base64, reversed, then XOR-decoded with
  // a key derived from the response hostname. The visible /troll/ HLS is a decoy.
  const dynamic = source.match(/\}\)\(["']([A-Za-z0-9+/=_-]{50,})["']\)/);
  if (dynamic && source.includes("reverse().join")) {
    const encoded = dynamic[1].replace(/-/g, "+").replace(/_/g, "/");
    let binary = "";
    try { binary = atob(encoded); } catch (_) {}
    if (binary) {
      let hostHash = 0;
      for (let index = 0; index < hostname.length; index += 1) {
        hostHash = (hostHash + hostname.charCodeAt(index)) & 255;
      }
      const reversed = binary.split("").reverse().join("");
      let decoded = "";
      for (let index = 0; index < reversed.length; index += 1) {
        const key = (0x3d + index * 89 + hostHash) & 255;
        decoded += String.fromCharCode(reversed.charCodeAt(index) ^ key);
      }
      if (/^https?:\/\//i.test(decoded) && /\.m3u8(?:[?#]|$)/i.test(decoded) && !/\/troll\//i.test(decoded)) {
        videoUrl = decoded;
      }
    }
  }

  // Legacy family: static repeating XOR key stored directly in the player JS.
  if (!videoUrl) {
    const legacy = /(?:var|let|const)\s+k=\[([0-9,\s]+)\],b=atob\(s\)[\s\S]*?return\s+\w+\}\)\(["']([A-Za-z0-9+/=_-]+)["']\)/g;
    let match, scanned = 0;
    while ((match = legacy.exec(source)) !== null && scanned++ < 8) {
      const keys = match[1].split(",").map(value => Number.parseInt(value.trim(), 10)).filter(Number.isFinite).slice(0, 64);
      if (!keys.length) continue;
      const encoded = match[2].replace(/-/g, "+").replace(/_/g, "/");
      let binary = "";
      try { binary = atob(encoded); } catch (_) { continue; }
      let decoded = "";
      for (let index = 0; index < binary.length; index += 1) {
        decoded += String.fromCharCode(binary.charCodeAt(index) ^ keys[index % keys.length]);
      }
      if (/^https?:\/\//i.test(decoded) && /\.m3u8(?:[?#]|$)/i.test(decoded) && !/\/troll\//i.test(decoded)) {
        videoUrl = decoded;
        break;
      }
    }
  }
  return videoUrl;
}
'''
    text = _once(text, crawler_anchor, helper + crawler_anchor, "v21-player-helper")

    start = text.index(crawler_anchor)
    end = text.index("\nfunction ", start + len(crawler_anchor))
    crawler = text[start:end]
    old_direct = "      const direct = urls.filter(_directMedia);\n"
    new_direct = '''      const decodedObfuscatedHls = playerText
        ? _spv21DecodedObfuscatedHls(playerText, responseUrl) : "";
      if (decodedObfuscatedHls) {
        streams.push(..._streams([decodedObfuscatedHls], responseUrl));
        continue;
      }
      // Never promote the known content-shape decoy as a direct stream.
      urls = urls.filter(url => !/\/troll\/master\.m3u8(?:[?#]|$)/i.test(_text(url)));
      const direct = urls.filter(_directMedia);
'''
    if crawler.count(old_direct) != 1:
        raise AssertionError(f"v21-crawler-direct-anchor: expected one anchor, got {crawler.count(old_direct)}")
    crawler = crawler.replace(old_direct, new_direct, 1)
    text = text[:start] + crawler + text[end:]

    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return True


def validate_base(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    v2051.validate_base(value)
    for needle in (
        MARKER,
        TRACE_MARKER,
        PLAYER_MARKER,
        "function _spv21DecodedObfuscatedHls",
        "globalThis.__nuvioProviderValueTraceHistoryV21",
        "while (history.length > 48) history.shift();",
        "const decodedObfuscatedHls = playerText",
        "! /troll/".replace(" ", ""),
    ):
        if needle not in value:
            # The decoy assertion below uses the concrete regex rather than this
            # readability token.
            if needle == "!/troll/":
                continue
            raise AssertionError(f"V21 ProviderBase missing {needle}")
    if '/\\/troll\\/master\\.m3u8' not in value:
        raise AssertionError("V21 decoy HLS rejection missing")
    window = value[value.index(MARKER): value.index("async function _resolveProviderValuePlan", value.index(MARKER))]
    lowered = window.casefold()
    for forbidden in ("animesama", "animevostfr", "french-manga", "vidzy", "fsvid", "purstream", "jujutsu"):
        if forbidden in lowered:
            raise AssertionError(f"V21 provider/host-specific token leaked: {forbidden}")
    trace_window = value[value.index(TRACE_MARKER): value.index("async function _resolveProviderValuePlan", value.index(TRACE_MARKER))].casefold()
    for forbidden in ("authorization", "cookie", "set-cookie", "responsebody", "requestheaders"):
        if forbidden in trace_window:
            raise AssertionError(f"V21 trace leaks forbidden field {forbidden}")


def main() -> int:
    changed = patch_worker() | patch_proof() | patch_recovery() | patch_materializer() | patch_base()
    validate_worker()
    validate_proof()
    validate_recovery()
    validate_materializer()
    validate_base()
    print(
        f"PROVIDER_SHARED_PLAYER_TRACE_V21_OK changed={str(changed).lower()} "
        "obfuscated_hls=1 decoy_hls_rejected=1 bounded_plan_trace=48 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
