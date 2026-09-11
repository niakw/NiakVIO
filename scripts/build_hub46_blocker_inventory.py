#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "automation/evidence/hub-lab-matrix-46.json"
MANIFEST = ROOT / "manifest.json"
OVERRIDES = ROOT / "provider-overrides.json"
KNOWLEDGE = ROOT / "automation/provider-v3-static-knowledge.json"
OUT_JSON = ROOT / "automation/evidence/hub46-blocker-inventory-20260911.json"
OUT_MD = ROOT / "automation/HUB46-BLOCKER-INVENTORY-20260911.md"
EXEC_ROUTE_KINDS = {"search", "detail", "api", "player", "source", "episode-index"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def uniq(values: list[object]) -> list[str]:
    out: list[str] = []
    for raw in values:
        value = str(raw or "").strip()
        if value and value not in out:
            out.append(value)
    return out


def route_kind(route: object) -> str:
    value = str(route or "").strip().casefold()
    if not value:
        return "ignore"
    if re.search(r"/(?:search|recherche)(?:[/?#]|$)|[?&](?:s|q|query|keyword|search|story)=", value):
        return "search"
    if re.search(r"/template-php/[^?#]*fetch\.php(?:[?#]|$)", value):
        return "search"
    if re.search(r"/(?:video[-_]?player|watchplayer|iframeplayer|player|embed|play)(?:[/?#.-]|$)", value):
        return "player"
    if re.search(r"/(?:download|file|mediafile|stream|getsource|get-source|source|sources)(?:[/?#.&_-]|$)", value):
        return "source"
    if re.search(r"/(?:episodes?(?:\.js|\.json|\.txt)?|season-list|episode-list)(?:[/?#.-]|$)", value):
        return "episode-index"
    if re.search(r"/api(?:[./?#]|$)|api\.", value):
        return "api"
    if re.search(
        r"\{(?:id|tmdb|tmdb_id|tmdbid|imdb|imdb_id|imdbid|title|query|slug|season|episode)\}|"
        r"/(?:title|movie|movies|film|films|tv|serie|series|show|watch|media|anime|animes|voir-series|episode|saison|season|saga|catalogue)(?:[/?#.-]|$)",
        value,
    ):
        return "detail"
    return "other"


def host(url: object) -> str:
    value = str(url or "").strip().casefold()
    match = re.match(r"^https?://([^/:?#]+)", value)
    return match.group(1).rstrip(".") if match else ""


def discovery_only(url: object) -> bool:
    h = host(url)
    return h in {"t.me", "telegram.me", "telegram.dog"} or h.endswith((".t.me", ".telegram.me", ".telegram.dog"))


def lane_texts(matrix_row: dict[str, Any]) -> list[str]:
    values: list[str] = []
    cells = matrix_row.get("cells") if isinstance(matrix_row.get("cells"), dict) else {}
    for fixture in cells.values():
        if not isinstance(fixture, dict):
            continue
        for text in fixture.values():
            values.append(str(text or ""))
    return values


def evidence_blocker(matrix_row: dict[str, Any]) -> str:
    text = " | ".join(lane_texts(matrix_row) + [str(matrix_row.get("overall") or ""), str(matrix_row.get("cause") or "")]).casefold()
    if "player ready" in text and "divergence runtime" in text:
        return "cross-runtime-divergence"
    if "hls 403" in text or ("403" in text and "stream" in text):
        return "stream-transport-403"
    if "faux positif" in text or "wrong content" in text or "identity" in text and "contradiction" in text:
        return "content-identity"
    if "provider_hard_timeout" in text or "timeout" in text:
        return "network-or-antibot-timeout"
    if "skipped despite declared capability" in text:
        return "capability-or-harness-skip"
    if "0 stream" in text:
        return "route-or-extraction-no-stream"
    if "player" in text and ("fail" in text or "error" in text):
        return "native-player"
    return "unclassified-evidence"


def mechanism_for(*, strategy: str, recipe: dict[str, Any], legos: list[str], route_kinds: set[str], authorities: list[str]) -> str:
    recipe_kind = str(recipe.get("recipeKind") or recipe.get("recipe_kind") or "").strip().casefold()
    if recipe:
        if recipe_kind == "typed-resolver-api":
            return "typed-resolver-api"
        return "api-recipe"
    if legos:
        return "provider-lego"
    if "search" in route_kinds and route_kinds & {"detail", "player", "source", "episode-index", "api"}:
        return "search-detail-extraction"
    if "api" in route_kinds:
        return "api-route"
    if route_kinds & {"player", "source"}:
        return "player-or-source-route"
    if "detail" in route_kinds and strategy == "html_scraper":
        return "html-detail-scraper"
    if strategy == "iframe_player" and authorities:
        return "iframe-player"
    if strategy == "direct_media" and authorities:
        return "direct-media-site"
    if strategy == "official_domain_hub":
        return "discovery-hub-only"
    if authorities:
        return "known-site-no-executable-route"
    return "unknown"


def main() -> int:
    matrix = load(MATRIX)
    manifest = load(MANIFEST)
    overrides = load(OVERRIDES)
    knowledge = load(KNOWLEDGE)

    manifest_rows = {
        cid(row.get("id")): row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and cid(row.get("id"))
    }
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    capabilities = overrides.get("provider_capabilities") if isinstance(overrides.get("provider_capabilities"), dict) else {}
    static_rows = knowledge.get("providers") if isinstance(knowledge.get("providers"), dict) else {}

    source_rows = matrix.get("rows") if isinstance(matrix.get("rows"), list) else []
    if int(matrix.get("hubCount") or 0) != 46 or len(source_rows) != 46:
        raise AssertionError(f"hub matrix must be exhaustive 46/46, got hubCount={matrix.get('hubCount')} rows={len(source_rows)}")

    out_rows: list[dict[str, Any]] = []
    opaque: list[str] = []
    mechanism_counts: Counter[str] = Counter()
    blocker_counts: Counter[str] = Counter()

    for source in source_rows:
        provider = cid(source.get("manifestId"))
        if provider not in manifest_rows:
            raise AssertionError(f"matrix provider missing from manifest: {provider}")
        entry = manifest_rows[provider]
        patch = patches.get(provider) if isinstance(patches.get(provider), dict) else {}
        capability = capabilities.get(provider) if isinstance(capabilities.get(provider), dict) else {}
        static_row = static_rows.get(provider) if isinstance(static_rows.get(provider), dict) else {}
        model = static_row.get("model") if isinstance(static_row.get("model"), dict) else {}

        strategy = str(patch.get("capability") or capability.get("strategy") or model.get("strategy") or "unknown").strip().casefold()
        recipe = patch.get("api_recipe") if isinstance(patch.get("api_recipe"), dict) else {}
        if not recipe and isinstance(model.get("apiRecipe"), dict):
            recipe = model.get("apiRecipe") or {}
        legos = uniq(list(patch.get("provider_lego_scripts") or []))

        routes = uniq(
            list(patch.get("learned_routes") or [])
            + list(capability.get("routes") or [])
            + list(model.get("routes") or [])
        )
        route_kinds = {route_kind(route) for route in routes} - {"ignore"}

        authority_candidates = uniq([
            patch.get("official_site"),
            patch.get("official_api"),
            (patch.get("fixed_endpoint") or {}).get("api") if isinstance(patch.get("fixed_endpoint"), dict) else None,
            model.get("knownSite"), model.get("officialSite"), model.get("officialApi"), model.get("fixedApi"),
            *(model.get("origins") or []),
        ])
        authorities = [value for value in authority_candidates if not discovery_only(value)]

        disposition = patch.get("repair_disposition") if isinstance(patch.get("repair_disposition"), dict) else {}
        mechanism = mechanism_for(
            strategy=strategy,
            recipe=recipe,
            legos=legos,
            route_kinds=route_kinds,
            authorities=authorities,
        )
        repo_opaque = mechanism in {"unknown", "discovery-hub-only", "known-site-no-executable-route"}
        opaque_reasons: list[str] = []
        if repo_opaque:
            if not recipe:
                opaque_reasons.append("no_api_recipe")
            if not legos:
                opaque_reasons.append("no_provider_lego")
            if not (route_kinds & EXEC_ROUTE_KINDS):
                opaque_reasons.append("no_executable_route_shape")
            if not authorities:
                opaque_reasons.append("no_nonhub_execution_authority")
            if source.get("hubRelation") == "registry-only":
                opaque_reasons.append("registry_only_hub")

        blocker = evidence_blocker(source)
        mechanism_counts[mechanism] += 1
        blocker_counts[blocker] += 1
        if repo_opaque:
            opaque.append(provider)

        out_rows.append({
            "provider": provider,
            "enabled": entry.get("enabled") is True,
            "hub": source.get("hub"),
            "officialHub": source.get("officialHub"),
            "hubRelation": source.get("hubRelation"),
            "strategy": strategy,
            "mechanism": mechanism,
            "repoOpaque": repo_opaque,
            "opaqueReasons": opaque_reasons,
            "executionAuthorities": authorities,
            "routeKinds": sorted(route_kinds),
            "routes": routes,
            "apiRecipeKind": str(recipe.get("recipeKind") or recipe.get("recipe_kind") or "") or None,
            "providerLegos": legos,
            "routeDataState": disposition.get("routeDataState"),
            "missingLanes": disposition.get("missingLanes") or [],
            "reasonCodes": disposition.get("reasonCodes") or [],
            "evidenceBlocker": blocker,
            "labOverall": source.get("overall"),
            "labCause": source.get("cause"),
            "cells": source.get("cells") or {},
        })

    enabled = [row["provider"] for row in out_rows if row["enabled"]]
    if len(enabled) != 46:
        raise AssertionError(f"hub46 inventory must contain exactly 46 enabled targets, got {len(enabled)}")

    report = {
        "schemaVersion": 1,
        "authority": "hub46-mechanism-blocker-inventory-v1",
        "providerCount": len(out_rows),
        "enabledTargetCount": len(enabled),
        "repoOpaqueCount": len(opaque),
        "repoOpaqueProviders": opaque,
        "mechanismCounts": dict(sorted(mechanism_counts.items())),
        "blockerCounts": dict(sorted(blocker_counts.items())),
        "rows": out_rows,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Hub46 — mechanism / blocker inventory — 2026-09-11",
        "",
        "This report distinguishes a provider that currently returns zero streams from a provider whose site mechanism is genuinely not demonstrated by current repository evidence.",
        "",
        f"- Targets: **{len(out_rows)}/46**.",
        f"- Enabled in canonical manifest: **{len(enabled)}/46**.",
        f"- Repository-evidence opaque candidates: **{len(opaque)}**.",
        "- `repoOpaque=true` is a research queue, not a declaration that the provider is dead.",
        "",
        "## Opaque candidates from repository evidence",
        "",
    ]
    if opaque:
        for row in out_rows:
            if row["repoOpaque"]:
                lines.append(
                    f"- **{row['provider']}** — mechanism `{row['mechanism']}`; "
                    f"reasons: {', '.join(row['opaqueReasons']) or 'unspecified'}; "
                    f"hub relation: `{row['hubRelation']}`; blocker: `{row['evidenceBlocker']}`."
                )
    else:
        lines.append("- None from repository evidence.")

    lines += [
        "",
        "## All 46",
        "",
        "| Provider | Mechanism | Repo opaque | Lab blocker | Route state | Hub relation |",
        "|---|---|---:|---|---|---|",
    ]
    for row in out_rows:
        lines.append(
            f"| {row['provider']} | {row['mechanism']} | {'yes' if row['repoOpaque'] else 'no'} | "
            f"{row['evidenceBlocker']} | {row['routeDataState'] or 'unknown'} | {row['hubRelation']} |"
        )

    lines += [
        "",
        "## Counts",
        "",
        "### Mechanisms",
        "",
    ]
    for key, value in sorted(mechanism_counts.items()):
        lines.append(f"- `{key}`: {value}")
    lines += ["", "### Current evidence blockers", ""]
    for key, value in sorted(blocker_counts.items()):
        lines.append(f"- `{key}`: {value}")
    lines += [
        "",
        "## Interpretation",
        "",
        "- `route-or-extraction-no-stream` does **not** mean opaque: routes/strategy may be understood but currently fail to yield a stream.",
        "- `cross-runtime-divergence` means at least one native runtime proved the provider while another failed; prioritize common runtime/bridge analysis before provider-specific rewrites.",
        "- `repoOpaque=true` means current structured DATA does not establish a credible execution mechanism; those providers should be investigated manually/web-side and returned to the user by name if still unresolved.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(
        "HUB46_BLOCKER_INVENTORY_OK "
        f"providers={len(out_rows)} enabled={len(enabled)} opaque={len(opaque)} "
        f"mechanisms={json.dumps(dict(sorted(mechanism_counts.items())), sort_keys=True)}"
    )
    if opaque:
        print("HUB46_REPO_OPAQUE " + ",".join(opaque))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
