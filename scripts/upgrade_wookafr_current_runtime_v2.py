#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
SCRIPT = "scripts/provider_patches/wookafr_current_runtime_v2.py"


def load() -> dict[str, Any]:
    value = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    row = (value.get("provider_patches") or {}).get("wookafr")
    if not isinstance(row, dict):
        raise AssertionError("provider-overrides missing wookafr")
    return value


def main() -> int:
    value = load(); row = value["provider_patches"]["wookafr"]
    before = json.dumps(value, ensure_ascii=False, sort_keys=True)
    scripts = [str(v) for v in row.get("provider_lego_scripts") or [] if str(v).strip()]
    if SCRIPT not in scripts:
        scripts.append(SCRIPT)
    row["provider_lego_scripts"] = scripts
    row.setdefault("provider_lego_options", {})[SCRIPT] = {}
    row["official_site"] = "https://wookafr.boston"
    row["capability"] = "mixed_embed_resolver"
    row["preserve_embed_urls"] = True
    routes = [str(v) for v in row.get("learned_routes") or []]
    for route in ("/?s={title}", "/streaming/{category}/{slug}/", "/streaming/series/{slug}/", "/streaming/episodes/{slug}-saison-{season}-episode-{episode}/", "https://lecteurvideo.com/embed.php?id={id}&tp={type}&url={source}"):
        if route not in routes: routes.append(route)
    row["learned_routes"] = routes
    notes = [str(v) for v in row.get("notes") or []]
    note = "Current-first Wooka runtime is authoritative before generic crawl: WP ?s= title search, strict movie-vs-series identity, exact season/episode route, then lecteurvideo showVideo(base64) players. No fixture ID or title is hardcoded."
    if note not in notes: notes.append(note)
    row["notes"] = notes
    after = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if before != after:
        OVERRIDES.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    check = load()["provider_patches"]["wookafr"]
    assert SCRIPT in check.get("provider_lego_scripts", [])
    assert set(str(v).lower() for v in check.get("published_types") or []) == {"movie", "tv"}
    assert check.get("official_site") == "https://wookafr.boston"
    print("WOOKAFR_CURRENT_RUNTIME_V2_OK changed=" + str(before != after).lower())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
