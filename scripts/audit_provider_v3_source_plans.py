#!/usr/bin/env python3
"""Audit whether each Provider v3 row owns a coherent executable plan.

Unlike the legacy strategy contract, a random route plus a base URL is not
counted as an executable provider plan. This report distinguishes deterministic
provider Lego/API recipes from heuristic generic-route fallbacks.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "automation" / "provider-v3-source-plan-audit.json"


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def useful_route(value: object) -> bool:
    text = str(value or "").strip()
    low = text.casefold()
    if not text or "${" in text or "encodeuricomponent(" in low:
        return False
    if "q=ponyfill" in low or low.rstrip("/") in {"/license", "license"}:
        return False
    return True


def route_kind(value: object) -> str:
    text = str(value or "").strip().casefold()
    if re.search(r"/api(?:[/?#.]|$)", text):
        return "api"
    if re.search(r"/(?:player|embed|play)(?:[/?#.-]|$)", text):
        return "player"
    if re.search(r"/(?:search|recherche)(?:[/?#]|$)|[?&](?:s|q|query|keyword)=", text):
        return "search"
    if re.search(r"\{(?:id|tmdb|tmdbid|tmdb_id|title|slug)\}|/(?:title|movie|film|tv|series|watch|media)(?:[/?#]|$)", text):
        return "detail"
    if "episodes.js" in text:
        return "episode-index"
    return "other"


def main() -> int:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    overrides = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
    knowledge = json.loads((ROOT / "automation/provider-v3-static-knowledge.json").read_text(encoding="utf-8"))
    rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict)]
    patches = overrides.get("provider_patches") or {}
    capabilities = overrides.get("provider_capabilities") or {}
    static = knowledge.get("providers") or {}
    report: list[dict[str, Any]] = []
    states = Counter()
    families = Counter()

    for row in rows:
        provider_id = cid(row.get("id"))
        patch = patches.get(provider_id) if isinstance(patches.get(provider_id), dict) else {}
        capability = capabilities.get(provider_id) if isinstance(capabilities.get(provider_id), dict) else {}
        static_row = static.get(provider_id) if isinstance(static.get(provider_id), dict) else {}
        model = static_row.get("model") if isinstance(static_row.get("model"), dict) else {}
        knowledge_row = static_row.get("knowledge") if isinstance(static_row.get("knowledge"), dict) else {}
        strategy = str(patch.get("capability") or capability.get("strategy") or model.get("strategy") or "unknown").strip().casefold()
        legos = [str(v).strip() for v in patch.get("provider_lego_scripts") or [] if str(v).strip()]
        recipe = patch.get("api_recipe") if isinstance(patch.get("api_recipe"), dict) else model.get("apiRecipe") if isinstance(model.get("apiRecipe"), dict) else None
        routes: list[str] = []
        for source in (patch.get("learned_routes"), capability.get("routes"), model.get("routes")):
            for raw in source if isinstance(source, list) else []:
                value = str(raw or "").strip()
                if useful_route(value) and value not in routes:
                    routes.append(value)
        kinds = sorted({route_kind(v) for v in routes} - {"other"})
        family = str(model.get("sourceRuntimeFamily") or knowledge_row.get("runtimeFamily") or "unknown").strip().casefold()
        if family:
            families[family] += 1

        if strategy == "quarantined":
            state = "quarantined"
            reason = "explicit quarantine"
        elif legos:
            state = "deterministic"
            reason = "provider Lego"
        elif recipe:
            required = bool(recipe.get("directRoute") or recipe.get("movieRoute") or recipe.get("episodeRoute"))
            if required:
                state = "deterministic"
                reason = "structured API recipe"
            else:
                state = "incomplete"
                reason = "API recipe without terminal route"
        elif family in {"stremio-json", "api-search-stream", "tmdb-direct-api"} and "api" in kinds:
            state = "family-plan-candidate"
            reason = f"recognized source family {family}, not materialized as Lego/recipe"
        elif family in {"catalogue-episodes-js", "signed-player-api", "catalogue-html-embed"}:
            state = "family-plan-candidate"
            reason = f"recognized source family {family}, not materialized as Lego/recipe"
        elif strategy in {"api_stream_resolver", "direct_media"} and "api" in kinds and any("{id}" in r or "{tmdb" in r.casefold() for r in routes):
            state = "heuristic"
            reason = "generic direct API route only"
        elif {"search", "detail"}.issubset(set(kinds)) or {"search", "player"}.issubset(set(kinds)):
            state = "heuristic"
            reason = "generic crawler route chain only"
        else:
            state = "incomplete"
            reason = "no coherent terminal plan"
        states[state] += 1
        report.append({
            "providerId": provider_id,
            "enabled": row.get("enabled") is not False,
            "strategy": strategy,
            "state": state,
            "reason": reason,
            "sourceRuntimeFamily": family,
            "providerLegos": legos,
            "hasApiRecipe": bool(recipe),
            "routeKinds": kinds,
            "routeCount": len(routes),
        })

    payload = {
        "schemaVersion": 1,
        "providerCount": len(rows),
        "states": dict(sorted(states.items())),
        "sourceRuntimeFamilies": dict(sorted(families.items())),
        "providers": report,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PROVIDER_V3_SOURCE_PLAN_AUDIT " + " ".join(f"{k}={v}" for k, v in sorted(states.items())))
    for row in report:
        if row["state"] not in {"deterministic", "quarantined"}:
            print(f"PLAN_GAP provider={row['providerId']} state={row['state']} family={row['sourceRuntimeFamily']} kinds={','.join(row['routeKinds'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
