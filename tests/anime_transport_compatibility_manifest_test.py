#!/usr/bin/env python3
"""Keep anime semantic capability distinct from Nuvio launch compatibility."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
VALID = {"movie", "tv", "anime"}
REQUIRED_ANIME_TRANSPORT = {"anime", "tv", "movie"}


def types(value: object) -> set[str]:
    rows = value if isinstance(value, list) else []
    return {
        str(item or "").strip().casefold()
        for item in rows
        if str(item or "").strip().casefold() in VALID
    }


rows = [row for row in MANIFEST.get("scrapers") or [] if isinstance(row, dict)]
assert len(rows) == 96, f"expected 96 providers, got {len(rows)}"

anime_rows = 0
errors: list[str] = []
for row in rows:
    provider = str(row.get("id") or "").strip() or "<missing>"
    supported = types(row.get("supportedTypes"))
    canonical_declared = "canonicalSupportedTypes" in row
    canonical = types(row.get("canonicalSupportedTypes")) if canonical_declared else supported

    # `anime` on the launch surface must represent real anime capability, never
    # an arbitrary transport alias attached to a non-anime provider.
    if "anime" in supported and "anime" not in canonical:
        errors.append(
            f"{provider}: supportedTypes exposes anime without canonical anime capability: "
            f"canonical={sorted(canonical)} supported={sorted(supported)}"
        )

    if "anime" not in canonical:
        continue

    anime_rows += 1
    missing = sorted(REQUIRED_ANIME_TRANSPORT - supported)
    if missing:
        errors.append(
            f"{provider}: anime launch compatibility missing={missing} "
            f"canonical={sorted(canonical)} supported={sorted(supported)}"
        )

    # Transport aliases may broaden `supportedTypes`, but they must not be copied
    # back into canonical capability. In particular, anime-only providers remain
    # canonical anime even though Nuvio may launch them through movie/tv lanes.
    if canonical_declared and canonical == {"anime"} and supported != REQUIRED_ANIME_TRANSPORT:
        errors.append(
            f"{provider}: anime-only semantic/transport split drift: "
            f"canonical={sorted(canonical)} supported={sorted(supported)}"
        )

assert anime_rows > 0, "manifest contains no canonical anime providers"
assert not errors, "anime semantic/transport contract failures:\n- " + "\n- ".join(errors)

print(
    "anime semantic/transport manifest contract passed: "
    f"providers=96 canonical_anime={anime_rows} required_transport=anime,tv,movie"
)
