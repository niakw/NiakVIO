#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
base = (ROOT / "scripts" / "provider_base_store.py").read_text(encoding="utf-8")
migration = (ROOT / "scripts" / "upgrade_provider_source_plan_v12.py").read_text(encoding="utf-8")

for marker in (
    "NIAKVIO_PROVIDER_SOURCE_PLAN_V12",
    "240 - extras.length * 60",
    '!["tv", "series", "show", "anime"].includes(token)',
    "movie|film|specials?|ova|ona",
    "download|file|files",
):
    assert marker in base, marker

# V12 must remain family-level: live diagnostics motivated the shape, but runtime
# code may not pin either provider or resolver host by name.
for forbidden in ("animekai", "anikai.cc", "movies4u", "m4uplay.store"):
    assert forbidden not in migration.casefold(), forbidden


def reference_title_bonus(leaf: str, title_slug: str) -> int:
    title_tokens = [v for v in title_slug.split("-") if v]
    leaf_tokens = [v for v in re.split(r"[^a-z0-9]+", leaf.casefold()) if v]
    if any(token not in leaf_tokens for token in title_tokens):
        return 0
    title = set(title_tokens)
    extras = [
        token for token in leaf_tokens
        if token not in title
        and token not in {"tv", "series", "show", "anime"}
        and not re.fullmatch(r"\d{4}", token)
    ]
    return max(-120, 240 - len(extras) * 60)


# A canonical TV-labelled result must outrank spin-off/sequel-shaped URLs when all
# share the exact title tokens. Season/media penalties in the real JS add further
# separation on top of this generic distance bonus.
canonical = reference_title_bonus("jujutsu-kaisen-tv", "jujutsu-kaisen")
sequel = reference_title_bonus("jujutsu-kaisen-2nd-season", "jujutsu-kaisen")
spin_off = reference_title_bonus("jujutsu-kaisen-the-culling-game-part-1", "jujutsu-kaisen")
assert canonical > sequel > spin_off, (canonical, sequel, spin_off)

# `/file/<opaque-id>` is only made crawl-eligible. The migration must not add it to
# direct-media extensions or return it as a stream by itself.
assert "file|files" in base
assert not re.search(r"directMedia[^\n]{0,300}file\|files", base, re.I), "file resolver leaked into direct media"

print("provider source plan v12 regression passed")
