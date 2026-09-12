#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_base_store.py"


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    marker = "NIAKVIO_PROVIDER_EXPLICIT_PLAYER_PAYLOAD_V24_2"
    if marker in text:
        print("PROVIDER_PLAYER_PAYLOAD_V24_2_OK changed=false")
        return 0
    old = r'''  const re = /(?:showVideo|loadVideo|setVideo|playVideo)\s*\(\s*["']([A-Za-z0-9+/_=-]{12,4096})["']\s*\)/gi;
'''
    new = r'''  /* NIAKVIO_PROVIDER_EXPLICIT_PLAYER_PAYLOAD_V24_2 */
  const re = /(?:showVideo|loadVideo|setVideo|playVideo)\s*\(\s*["']([A-Za-z0-9+/_=-]{12,4096})["']\s*(?:,\s*["']?\d{1,4}["']?)?\s*\)/gi;
'''
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"explicit player regex anchor count={count}")
    TARGET.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("PROVIDER_PLAYER_PAYLOAD_V24_2_OK changed=true optional_priority_arg=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
