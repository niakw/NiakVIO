#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from upstream_identity_guard import classify_route_identity  # noqa: E402


def raw(url: str) -> dict:
    return {"network_observations": [{"stage": "content_lookup", "proof_url": url}]}


def expect(title: str, url: str, status: str) -> None:
    got = classify_route_identity(raw(url), {"title": title})
    assert got["status"] == status, (title, url, got)


def main() -> int:
    # Live false positives proven during Hub46 recovery.
    expect("Superman", "https://animevostfr.org/animes/neon-genesis-evangelion/", "CONTRADICTION")
    expect("Sinners", "https://animesama.co/anime/the-garden-of-sinners.html", "CONTRADICTION")
    expect("Joker", "https://voir-anime.to/anime/joker-game/", "CONTRADICTION")

    # Historical user-visible wrong-media symptom.
    expect("Interstellar", "https://example.invalid/movie/interstellar-documentary-2014/", "CONTRADICTION")

    # Year/language/quality suffixes are not a different work.
    expect("Interstellar", "https://example.invalid/movie/interstellar-2014/", "MATCH")
    expect("Joker", "https://example.invalid/film/joker-vf/", "MATCH")

    # Multi-word aliases are deliberately not auto-rejected: translated/Japanese
    # aliases need a stronger Core identity source than route-token overlap.
    got = classify_route_identity(raw("https://example.invalid/anime/nanatsu-no-taizai/"), {"title": "The Seven Deadly Sins"})
    assert got["status"] == "UNKNOWN", got

    print("UPSTREAM_IDENTITY_GUARD_OK strong_wrong_work=4 exact_suffix=2 multiword_alias=unknown")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
