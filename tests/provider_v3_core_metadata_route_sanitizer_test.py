#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"
TMDB_ROUTE = re.compile(r"api\.themoviedb\.org|themoviedb\.org|^/api\.themoviedb\.org|^/3/(?:\{media\}|\{type\}|movie|tv)/\{tmdb(?:_?id)?\}.*[?&]api_key=", re.I)


def iter_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for child in value:
            yield from iter_strings(child)
    elif isinstance(value, dict):
        for child in value.values():
            yield from iter_strings(child)


def main() -> int:
    payload = json.loads(KNOWLEDGE.read_text(encoding="utf-8"))
    providers = payload.get("providers")
    assert isinstance(providers, dict) and len(providers) == 96
    assert payload.get("coreMetadataTransportSanitized") is True
    assert payload.get("coreMetadataTransportOwner") == "core"

    offenders = []
    for provider_id, row in providers.items():
        model = row.get("model") if isinstance(row, dict) else None
        knowledge = row.get("knowledge") if isinstance(row, dict) else None
        for section_name, section in (("model", model), ("knowledge", knowledge)):
            if not isinstance(section, dict):
                continue
            for key in ("routes", "routeFragments", "observedUrls", "origins"):
                if key not in section:
                    continue
                for raw in iter_strings(section.get(key)):
                    if TMDB_ROUTE.search(raw.strip().replace("\\/", "/")):
                        offenders.append((provider_id, section_name, key, raw))
        recipe = model.get("apiRecipe") if isinstance(model, dict) else None
        if isinstance(recipe, dict):
            for raw in iter_strings(recipe):
                if TMDB_ROUTE.search(raw.strip().replace("\\/", "/")):
                    offenders.append((provider_id, "model", "apiRecipe", raw))

    assert not offenders, "Core-owned TMDB transport leaked into Provider DATA: " + repr(offenders[:12])
    print("PROVIDER_V3_CORE_METADATA_ROUTE_SANITIZER_TEST_OK providers=96 tmdb_owner=core")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
