#!/usr/bin/env python3
"""Persist knowledge-only Provider v3 DATA extracted from historical/upstream JS.

This script never executes provider JavaScript. It consumes the static
`clean_provider_model` / `upstream_knowledge` records emitted by
`discover_candidates.py` and turns them into a durable reconstruction input.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STAGE = ROOT / "staging" / "provider-v3-static-knowledge"
DEFAULT_OUTPUT = ROOT / "automation" / "provider-v3-static-knowledge.json"
MANIFEST = ROOT / "manifest.json"
OVERRIDES = ROOT / "provider-overrides.json"
EXPECTED = 96


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: object required")
    return value


def canonical(value: object) -> str:
    return "".join(ch for ch in str(value or "").strip().casefold() if ch.isalnum() or ch in "-_")


NON_EXECUTABLE_MODEL_HOSTS = (
    "npms.io", "lodash.com", "openjsf.org", "underscorejs.org",
    "arm.haglund.dev", "v3-cinemeta.strem.io",
)


def model_url_allowed(value: object) -> bool:
    text = str(value or "").strip()
    lowered = text.casefold()
    if not text or "${" in text or "encodeURIComponent(" in text:
        return False
    return not any(host in lowered for host in NON_EXECUTABLE_MODEL_HOSTS)


def model_route_allowed(value: object) -> bool:
    text = str(value or "").strip()
    lowered = text.casefold()
    if not text or "${" in text or "encodeURIComponent(" in text:
        return False
    return "q=ponyfill" not in lowered and lowered.rstrip("/") != "/license"


def merge_list(target: list[str], values: object, limit: int) -> None:
    if not isinstance(values, list):
        return
    for raw in values:
        value = str(raw or "").strip()
        if not value or "old.invalid" in value:
            continue
        if value not in target:
            target.append(value)
        if len(target) >= limit:
            return


def merged_row(provider_id: str, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    model: dict[str, Any] = {
        "knownSite": None,
        "strategy": "unknown",
        "officialSite": None,
        "officialHub": None,
        "officialApi": None,
        "fixedApi": None,
        "origins": [],
        "observedUrls": [],
        "routes": [],
        "apiRecipe": None,
    }
    knowledge: dict[str, Any] = {
        "hosts": [],
        "routes": [],
        "routeFragments": [],
        "observedUrls": [],
        "decodedStaticStringCount": 0,
    }
    sources: list[dict[str, Any]] = []

    ordered = sorted(
        candidates,
        key=lambda row: (
            int(row.get("source_priority") or 9999),
            1 if str(row.get("source") or "") == "published-baseline" else 0,
            str(row.get("source") or ""),
        ),
    )
    for candidate in ordered:
        if candidate.get("upstream_code_executed") is not False:
            raise ValueError(f"{provider_id}: upstream executable knowledge forbidden")
        if candidate.get("legacy_provider_js_executed_for_reconstruction") is not False:
            raise ValueError(f"{provider_id}: legacy executable knowledge forbidden")
        cm = candidate.get("clean_provider_model")
        uk = candidate.get("upstream_knowledge")
        if not isinstance(cm, dict) or not isinstance(uk, dict):
            continue
        if uk.get("codeExecuted") is not False:
            raise ValueError(f"{provider_id}: static knowledge codeExecuted must be false")

        for key in ("knownSite", "officialSite", "officialHub", "officialApi", "fixedApi"):
            value = str(cm.get(key) or "").strip()
            if value and not model.get(key):
                model[key] = value
        strategy = str(cm.get("strategy") or "").strip().casefold()
        if model["strategy"] == "unknown" and strategy and strategy != "unknown":
            model["strategy"] = strategy
        if model.get("apiRecipe") is None and isinstance(cm.get("apiRecipe"), dict):
            model["apiRecipe"] = cm["apiRecipe"]

        merge_list(model["origins"], cm.get("origins"), 48)
        merge_list(model["observedUrls"], cm.get("observedUrls"), 72)
        merge_list(model["routes"], cm.get("routes"), 96)
        merge_list(knowledge["hosts"], uk.get("hosts"), 64)
        merge_list(knowledge["routes"], uk.get("routes"), 128)
        merge_list(knowledge["routeFragments"], uk.get("routeFragments"), 128)
        merge_list(knowledge["observedUrls"], uk.get("observedUrls"), 96)
        knowledge["decodedStaticStringCount"] += int(uk.get("decodedStaticStringCount") or 0)

        sources.append({
            "source": str(candidate.get("source") or ""),
            "sourceName": str(candidate.get("source_name") or ""),
            "upstreamId": str(candidate.get("upstream_id") or ""),
            "manifestOrigin": str(candidate.get("manifest_origin") or ""),
            "upstreamSha256": str(candidate.get("upstream_sha256") or ""),
            "codeRole": "knowledge-only",
            "codeExecuted": False,
        })

    # Static route extraction is authoritative knowledge when the cleaned model
    # missed it. It remains DATA, never executable code.
    merge_list(model["routes"], knowledge["routes"], 96)
    merge_list(model["observedUrls"], knowledge["observedUrls"], 72)
    for host in knowledge["hosts"]:
        value = "https://" + host
        if value not in model["origins"] and not value.endswith(".invalid"):
            model["origins"].append(value)
        if len(model["origins"]) >= 48:
            break

    # Keep raw static knowledge as provenance, but only promote deterministic
    # provider-owned routes/origins into the executable model.
    model["origins"] = [value for value in model["origins"] if model_url_allowed(value)]
    model["observedUrls"] = [value for value in model["observedUrls"] if model_url_allowed(value)]
    model["routes"] = [value for value in model["routes"] if model_route_allowed(value)]

    return {
        "model": model,
        "knowledge": knowledge,
        "sources": sources,
        "legacyProviderJsExecuted": False,
        "upstreamJsExecuted": False,
    }


def has_execution_data(row: dict[str, Any], patch: dict[str, Any]) -> bool:
    model = row.get("model") if isinstance(row.get("model"), dict) else {}
    if isinstance(patch.get("provider_lego_scripts"), list) and patch["provider_lego_scripts"]:
        return True
    if isinstance(patch.get("api_recipe"), dict) or isinstance(model.get("apiRecipe"), dict):
        return True
    for key in ("knownSite", "officialSite", "officialApi", "fixedApi"):
        if str(model.get(key) or "").strip():
            return True
    return bool(model.get("routes")) and any(
        str(model.get(key) or "").strip()
        for key in ("knownSite", "officialSite", "officialHub", "officialApi", "fixedApi")
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, default=DEFAULT_STAGE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    manifest = load(MANIFEST)
    overrides = load(OVERRIDES)
    registry = load(args.stage.resolve() / "candidates.json")
    current = {
        canonical(row.get("id")): row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and canonical(row.get("id"))
    }
    if len(current) != EXPECTED:
        raise ValueError(f"manifest provider count={len(current)} expected={EXPECTED}")

    grouped: dict[str, list[dict[str, Any]]] = {provider_id: [] for provider_id in current}
    for candidate in registry.get("candidates") or []:
        if not isinstance(candidate, dict):
            continue
        provider_id = canonical(candidate.get("canonical_id"))
        if provider_id in grouped:
            grouped[provider_id].append(candidate)

    missing_candidates = sorted(provider_id for provider_id, values in grouped.items() if not values)
    if missing_candidates:
        raise ValueError(f"static knowledge candidate missing for providers={missing_candidates}")

    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    providers: dict[str, Any] = {}
    unusable: list[str] = []
    for provider_id in current:
        row = merged_row(provider_id, grouped[provider_id])
        patch = patches.get(provider_id) if isinstance(patches.get(provider_id), dict) else {}
        if not has_execution_data(row, patch):
            unusable.append(provider_id)
        providers[provider_id] = row

    if unusable:
        raise ValueError(
            "static DATA remains non-executable for providers="
            + ",".join(sorted(unusable))
        )

    output = {
        "schemaVersion": 1,
        "providerCount": len(providers),
        "source": "discover_candidates.static_knowledge",
        "role": "durable-structured-provider-data",
        "legacyProviderJsExecuted": False,
        "upstreamJsExecuted": False,
        "providers": providers,
    }
    target = args.output.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    routeful = sum(1 for row in providers.values() if row["model"].get("routes"))
    urlful = sum(1 for row in providers.values() if row["model"].get("observedUrls"))
    originful = sum(1 for row in providers.values() if row["model"].get("origins"))
    print(
        "FIELD_PROVIDER_V3_STATIC_KNOWLEDGE "
        f"providers={len(providers)} routes={routeful} urls={urlful} origins={originful} "
        "legacy_executed=false upstream_executed=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
