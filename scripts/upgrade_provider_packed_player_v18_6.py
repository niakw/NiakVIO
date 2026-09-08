#!/usr/bin/env python3
"""V18.6: decode generic Dean-Edwards packed player payloads before URL crawl.

This is a structural player capability, not a provider rule. Many embed players
serve their real media URL inside the common p,a,c,k,e,d packer shape. The clean
ProviderBase may decode that inert string representation, but must never eval or
execute upstream JavaScript.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_PACKED_PLAYER_V18_6"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch() -> bool:
    text = BASE.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False
    if "NIAKVIO_PROVIDER_BASE_CORRELATED_VALUE_PLAN_V18" not in text:
        raise AssertionError("V18.6 requires V18 correlated value plan")

    anchor = "async function _crawlDirectMedia(seedUrls, referer, maxDepth) {\n"
    helper = r'''/* NIAKVIO_PROVIDER_PACKED_PLAYER_V18_6 */
function _spv186UnpackPackedPlayer(code) {
  const source = _text(code);
  if (!source.includes("p,a,c,k,e,d")) return source;
  try {
    function blocks(input) {
      const out = [];
      let pos = 0;
      while (true) {
        const start = input.indexOf("eval(function(p,a,c,k,e,d)", pos);
        if (start < 0) break;
        let depth = 0, single = false, double = false, escaped = false, i = start;
        for (; i < input.length; i++) {
          const ch = input[i];
          if (escaped) { escaped = false; continue; }
          if (ch === "\\") { escaped = true; continue; }
          if (!double && ch === "'") single = !single;
          else if (!single && ch === '"') double = !double;
          if (single || double) continue;
          if (ch === "(") depth += 1;
          else if (ch === ")") {
            depth -= 1;
            if (depth === 0) { i += 1; break; }
          }
        }
        if (i > start) out.push(input.slice(start, i));
        pos = Math.max(i, start + 1);
      }
      return out.slice(0, 8);
    }
    function decodeString(src, start) {
      const quote = src[start];
      if (quote !== "'" && quote !== '"') return null;
      let out = "", escaped = false, i = start + 1;
      for (; i < src.length; i++) {
        const ch = src[i];
        if (escaped) {
          if (ch === "n") out += "\n";
          else if (ch === "r") out += "\r";
          else if (ch === "t") out += "\t";
          else out += ch;
          escaped = false;
          continue;
        }
        if (ch === "\\") { escaped = true; continue; }
        if (ch === quote) return { value: out, end: i + 1 };
        out += ch;
      }
      return null;
    }
    function skipWs(src, i) { while (i < src.length && /\s/.test(src[i])) i += 1; return i; }
    function integer(src, i) {
      i = skipWs(src, i);
      const match = src.slice(i).match(/^\d+/);
      return match ? { value: parseInt(match[0], 10), end: i + match[0].length } : null;
    }
    function decodeBlock(block) {
      const call = block.indexOf("}(");
      if (call < 0) return null;
      let i = skipWs(block, call + 2);
      const payload = decodeString(block, i);
      if (!payload) return null;
      i = skipWs(block, payload.end);
      if (block[i] !== ",") return null;
      const radixRow = integer(block, i + 1);
      if (!radixRow || radixRow.value < 2 || radixRow.value > 62) return null;
      const radix = radixRow.value;
      i = skipWs(block, radixRow.end);
      if (block[i] !== ",") return null;
      const countRow = integer(block, i + 1);
      if (!countRow || countRow.value > 10000) return null;
      let count = countRow.value;
      i = skipWs(block, countRow.end);
      if (block[i] !== ",") return null;
      const wordsRow = decodeString(block, skipWs(block, i + 1));
      if (!wordsRow) return null;
      if (!/^\s*\.split\(\s*['"]\|['"]\s*\)/.test(block.slice(wordsRow.end, wordsRow.end + 32))) return null;
      const words = wordsRow.value.split("|").slice(0, 10000);
      function key(value) {
        return (value < radix ? "" : key(parseInt(value / radix, 10)))
          + ((value = value % radix) > 35 ? String.fromCharCode(value + 29) : value.toString(36));
      }
      const dictionary = {};
      while (count-- > 0) dictionary[key(count)] = words[count] || key(count);
      return payload.value.replace(/\b\w+\b/g, word => dictionary[word] || word);
    }
    let result = source;
    for (const block of blocks(source)) {
      const decoded = decodeBlock(block);
      if (decoded) result = result.replace(block, decoded);
    }
    return result;
  } catch (_) {
    return source;
  }
}
'''
    text = once(text, anchor, helper + anchor, "v18.6-packed-player-helper")

    old = '''      } else {
        urls = _extractUrls(await response.text(), responseUrl);
      }
'''
    new = '''      } else {
        const playerText = await response.text();
        const decodedPlayerText = _spv186UnpackPackedPlayer(playerText);
        urls = _extractUrls(decodedPlayerText, responseUrl);
      }
'''
    text = once(text, old, new, "v18.6-player-decode-before-extract")
    BASE.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    if value.count(MARKER) != 1:
        raise AssertionError(f"V18.6 marker count={value.count(MARKER)}")
    for needle in (
        "function _spv186UnpackPackedPlayer(code)",
        'input.indexOf("eval(function(p,a,c,k,e,d)"',
        "radixRow.value > 62",
        "countRow.value > 10000",
        "const decodedPlayerText = _spv186UnpackPackedPlayer(playerText);",
        "urls = _extractUrls(decodedPlayerText, responseUrl);",
    ):
        if needle not in value:
            raise AssertionError(f"V18.6 missing {needle}")
    section = value.split("/* NIAKVIO_PROVIDER_PACKED_PLAYER_V18_6 */", 1)[1].split(
        "async function _crawlDirectMedia", 1
    )[0].casefold()
    for forbidden in (
        "mugiwara",
        "smoothpre",
        "ansembed",
        "jujutsu",
        "eval(",
        "new function",
    ):
        if forbidden in section and forbidden != "eval(":
            raise AssertionError(f"V18.6 provider-specific token leaked: {forbidden}")
    # The string literal naming the packer starts with 'eval(function'; actual
    # JavaScript evaluation primitives remain forbidden.
    if " eval(" in section or "=eval(" in section or "function(" + "eval" in section:
        raise AssertionError("V18.6 must never execute eval")


def main() -> int:
    changed = patch()
    print(
        f"PROVIDER_PACKED_PLAYER_V18_6_OK changed={str(changed).lower()} "
        "packer_decode=1 eval_execution=0 bounded_blocks=8 bounded_dictionary=10000 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
