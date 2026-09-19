#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "provider_base_store.py"


def main() -> int:
    text = BASE.read_text(encoding="utf-8")
    required = [
        "NIAKVIO_PROVIDER_EPISODE_HOP_V24",
        "const languageEpisode = path.match(",
        "(?:vostfr|vf|vff|vfq|vo)",
        "wantedSeason === 1 && Number(languageEpisode[1]) === wantedEpisode",
        "const exactEpisodeHop = await _spv22ResolveEpisodeHop(html, base, mediaType, season, episode);",
        "if (exactEpisodeHop.length) return exactEpisodeHop.slice(0, 40);",
        "NIAKVIO_PROVIDER_EXPLICIT_PLAYER_PAYLOAD_V24_1",
        "function _spv241ExplicitPlayerPayloadUrls(text, base)",
        "(?:showVideo|loadVideo|setVideo|playVideo)",
        "_spv241ExplicitPlayerPayloadUrls(decodedPlayerText, responseUrl)",
    ]
    for marker in required:
        assert marker in text, marker
    assert "if (parsed.origin !== baseUrl.origin) continue;" in text
    assert "if (!marker.marked || !marker.matches) continue;" in text
    v24 = text.split("NIAKVIO_PROVIDER_EPISODE_HOP_V24", 1)[1].split("return { marked: false", 1)[0]
    assert "languageEpisode" in v24
    assert "vostfr|vf|vff|vfq|vo" in v24
    payload = text.split("NIAKVIO_PROVIDER_EXPLICIT_PLAYER_PAYLOAD_V24_1", 1)[1].split("async function _crawlDirectMedia", 1)[0]
    assert "showVideo" in payload and "atob(encoded)" in payload
    assert "524288" in payload and "scanned++ < 24" in payload
    assert "[A-Za-z0-9+/_=-]{12,4096}" in payload
    print("provider episode hop v24/v24.1 tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
