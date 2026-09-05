#!/usr/bin/env python3
'''Sanitize executable Provider v3 routes after static knowledge enrichment.

The static extractors intentionally favor recall. This final pass removes
source-code/regex residue that must never be replayed as a network route, repairs
empty search parameters into explicit {query} placeholders, and promotes
protocol families when the route set itself gives strong evidence.
'''
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"
EXPECTED = 96

SEARCH_EMPTY_RE = re.compile(
    r"([?&](?:s|q|query|keyword|search|story)=)(?:\.{3})?(?=&|#|$)",
    re.I,
)
ASSET_RE = re.compile(r"\.(?:css|jpe?g|png|gif|webp|svg|avif|ico|woff2?|ttf)(?:[?#]|$)", re.I)
DOMAIN_LIST_RE = re.compile(r"/(?:refs/heads/[^/]+/)?domains?\.json(?:[?#]|$)", re.I)
REGEX_RESIDUE_RE = re.compile(
    r"(?:\(\?:|\(\?=|\(\?!|\\[dDsSwW][+*?]?|\[[^\]]*$|(?:^|[/_-])i\[$)",
    re.I,
)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: object required")
    return value


def balanced(value: str, left: str, right: str) -> bool:
    return value.count(left) == value.count(right)


def repair_route(raw: object) -> tuple[str, bool]:
    value = str(raw or "").strip().replace("\\/", "/")
    if not value:
        return "", False
    original = value
    value = SEARCH_EMPTY_RE.sub(lambda match: match.group(1) + "{query}", value)
    value = value.replace("?search=...&", "?search={query}&")
    value = re.sub(r"([?&](?:s|q|query|keyword|search|story)=)\.{3}(?=&|#|$)", r"\1{query}", value, flags=re.I)
    return value, value != original


def executable_route(raw: object) -> tuple[str, str]:
    value, _ = repair_route(raw)
    if not value or value == "/":
        return "", "empty"
    low = value.casefold()

    if not balanced(value, "{", "}") or not balanced(value, "[", "]") or not balanced(value, "(", ")"):
        return "", "unbalanced"
    if REGEX_RESIDUE_RE.search(value):
        return "", "regex_residue"
    if "${" in value or "encodeuricomponent(" in low or "decodeuricomponent(" in low:
        return "", "js_expression"
    if ASSET_RE.search(value):
        return "", "asset"
    if DOMAIN_LIST_RE.search(value):
        return "", "domain_discovery_not_runtime"
    if re.search(r"(?:^|[/?#&])(?:legal-considerations|privacy-policy|terms-of-service)(?:[/?#&=]|$)", low):
        return "", "non_runtime_page"
    if value.startswith("#"):
        return "", "fragment"
    if re.search(r"[?&](?:s|q|query|keyword|search|story)=(?:&|#|$)", value, re.I):
        return "", "empty_search"

    return value, ""


def clean_list(values: object) -> tuple[list[str], int, int, dict[str, int]]:
    if not isinstance(values, list):
        return [], 0, 0, {}
    out: list[str] = []
    removed = 0
    repaired = 0
    reasons: dict[str, int] = {}
    for raw in values:
        fixed, changed = repair_route(raw)
        route, reason = executable_route(fixed)
        if reason:
            removed += 1
            reasons[reason] = reasons.get(reason, 0) + 1
            continue
        if changed:
            repaired += 1
        if route not in out:
            out.append(route)
    return out, removed, repaired, reasons


def strong_family(model: dict[str, Any]) -> str:
    routes = [str(value or "") for value in model.get("routes") or []]
    joined = "\n".join(routes).casefold()

    if "/engine/ajax/film_api.php" in joined:
        return "dle-film-api"
    if "full-story.php" in joined:
        return "dle-full-story"
    if "controller.php?mod=playepisode" in joined:
        return "dle-playepisode-form"
    if "/stream/movie/" in joined and ("/stream/series/" in joined or "/stream/tv/" in joined):
        return "stremio-json"
    if "episodes.js" in joined and "/catalogue/" in joined:
        return "catalogue-episodes-js"
    return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--knowledge", type=Path, default=DEFAULT_KNOWLEDGE)
    args = parser.parse_args()
    path = args.knowledge.resolve()
    payload = load(path)
    providers = payload.get("providers")
    if not isinstance(providers, dict) or len(providers) != EXPECTED:
        raise ValueError(f"expected {EXPECTED} provider knowledge rows")

    removed = 0
    repaired = 0
    touched = 0
    family_promoted = 0
    reason_totals: dict[str, int] = {}

    for provider_id, row in providers.items():
        if not isinstance(row, dict):
            continue
        model = row.get("model") if isinstance(row.get("model"), dict) else {}
        knowledge = row.get("knowledge") if isinstance(row.get("knowledge"), dict) else {}
        local_changed = False

        for container, key in (
            (model, "routes"),
            (knowledge, "routes"),
            (knowledge, "routeFragments"),
        ):
            if not isinstance(container.get(key), list):
                continue
            before = list(container.get(key) or [])
            cleaned, local_removed, local_repaired, reasons = clean_list(before)
            container[key] = cleaned
            removed += local_removed
            repaired += local_repaired
            for reason, count in reasons.items():
                reason_totals[reason] = reason_totals.get(reason, 0) + count
            if cleaned != before:
                local_changed = True

        family = strong_family(model)
        if family:
            current = str(model.get("sourceRuntimeFamily") or "unknown").strip().casefold()
            if current != family:
                model["sourceRuntimeFamily"] = family
                knowledge["runtimeFamily"] = family
                family_promoted += 1
                local_changed = True

        for route in model.get("routes") or []:
            executable, reason = executable_route(route)
            if reason or executable != route:
                raise AssertionError(f"{provider_id}: unsafe route survived: {route!r} reason={reason}")

        row["model"] = model
        row["knowledge"] = knowledge
        if local_changed:
            touched += 1

    payload["executionRouteSanitized"] = True
    payload["executionRouteSanitizerVersion"] = 1
    payload["executionRouteSanitizerPolicy"] = "no-source-code-residue-empty-search-repaired"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    reasons = ",".join(f"{key}:{reason_totals[key]}" for key in sorted(reason_totals)) or "none"
    print(
        "PROVIDER_V3_EXECUTION_ROUTE_SANITIZE_OK "
        f"providers={len(providers)} touched={touched} removed={removed} repaired={repaired} "
        f"family_promoted={family_promoted} reasons={reasons}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
