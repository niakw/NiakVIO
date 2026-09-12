#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_base_store.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 anchor, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    marker = "NIAKVIO_PROVIDER_EXPLICIT_PLAYER_PRIORITY_V24_3"
    if marker in text:
        print("PROVIDER_PLAYER_PAYLOAD_V24_3_OK changed=false")
        return 0

    old = '''        const decodedPlayerText = _spv186UnpackPackedPlayer(playerText);\n        urls = _uniq(_extractUrls(decodedPlayerText, responseUrl).concat(\n          _spv241ExplicitPlayerPayloadUrls(decodedPlayerText, responseUrl)\n        ));\n      }\n      const decodedObfuscatedHls = playerText\n'''
    new = '''        const decodedPlayerText = _spv186UnpackPackedPlayer(playerText);\n        /* NIAKVIO_PROVIDER_EXPLICIT_PLAYER_PRIORITY_V24_3 */\n        const explicitPlayerUrls = _spv241ExplicitPlayerPayloadUrls(decodedPlayerText, responseUrl);\n        const ordinaryPlayerUrls = _extractUrls(decodedPlayerText, responseUrl);\n        urls = _uniq(explicitPlayerUrls.concat(ordinaryPlayerUrls));\n        if (explicitPlayerUrls.length) {\n          const explicitDirect = explicitPlayerUrls.filter(_directMedia);\n          if (explicitDirect.length) {\n            streams.push(..._streams(explicitDirect, responseUrl));\n            continue;\n          }\n          if (row.depth < Math.max(0, Number(maxDepth) || 0)) {\n            for (const nested of explicitPlayerUrls.filter(_crawlEligible).slice(0, 8)) {\n              const next = _crawlCanonical(nested);\n              if (next && !seen.has(next)) queue.push({ url: next, depth: row.depth + 1, referer: responseUrl });\n            }\n          }\n          // An explicit player handoff outranks incidental raw download links\n          // present elsewhere in the same HTML page. Process queued players\n          // before considering those ordinary direct-looking links.\n          if (queue.length) continue;\n        }\n      }\n      const decodedObfuscatedHls = playerText\n'''
    text = replace_once(text, old, new, "player priority")
    TARGET.write_text(text, encoding="utf-8")
    print("PROVIDER_PLAYER_PAYLOAD_V24_3_OK changed=true explicit_player_precedes_raw_download=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
