#!/usr/bin/env python3
"""Sanitized diagnostic for proof-correlated provider-value search identities.

This is workbench-only evidence. It replays only materialized providerValuePlan
search requests and persists bounded catalogue metadata shape: response type,
object keys, known identity-label scores and safe provider-id/slug candidates.
It never stores full response bodies, cookies, authorization headers or media URLs.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
YIELD = ROOT / "automation" / "provider-repair-fast-yield.json"
OUTPUT = ROOT / "automation" / "provider-value-identity-shape-v1.json"

LABEL_FIELDS = (
    "title", "name", "original_title", "post_title", "label", "anime",
    "movie", "series", "show", "matched", "display_name", "displayName",
)
ID_FIELDS = (
    "id", "ID", "_id", "media_id", "post_id", "anime_id", "movie_id",
    "series_id", "show_id", "slug", "provider_slug", "seo_slug",
)
SAFE_HEADERS = {
    "accept", "accept-language", "user-agent", "referer", "origin",
    "x-requested-with", "content-type",
}
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9._~-]{1,160}$")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def text(value: object, limit: int = 180) -> str:
    if value is None or isinstance(value, (dict, list, tuple)):
        return ""
    return str(value).strip()[:limit]


def slug(value: object) -> str:
    raw = unicodedata.normalize("NFD", text(value, 300)).casefold()
    raw = "".join(ch for ch in raw if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", raw).strip("-")


def title_score(actual: object, expected: object) -> int:
    a = slug(actual)
    e = slug(expected)
    if not a or not e:
        return 0
    if a == e:
        return 240
    if a in e or e in a:
        return 110
    return sum(18 for token in e.split("-") if len(token) >= 3 and token in a)


def json_rows(value: Any, out: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    out = out if out is not None else []
    if len(out) >= 300:
        return out
    if isinstance(value, list):
        for child in value:
            json_rows(child, out)
            if len(out) >= 300:
                break
        return out
    if not isinstance(value, dict):
        return out
    out.append(value)
    for child in value.values():
        if isinstance(child, (dict, list)):
            json_rows(child, out)
            if len(out) >= 300:
                break
    return out


def expand_scalar(value: Any, values: dict[str, object]) -> Any:
    if not isinstance(value, str):
        return value
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        replacement = values.get(key)
        return "" if replacement is None else str(replacement)
    return re.sub(r"\{([^}]+)\}", repl, value)


def expand_object(value: Any, values: dict[str, object]) -> Any:
    if isinstance(value, dict):
        return {str(k): expand_object(v, values) for k, v in value.items()}
    if isinstance(value, list):
        return [expand_object(v, values) for v in value]
    return expand_scalar(value, values)


def request(plan: dict[str, Any], query: str, timeout: float) -> tuple[int, str, bytes]:
    base = text(plan.get("searchBase"), 500)
    route = text(plan.get("searchRoute"), 1000)
    encoded = urllib.parse.quote(query, safe="")
    route = re.sub(r"\{(?:query|title|q)\}", encoded, route, flags=re.I)
    if not base.startswith(("http://", "https://")) or not route:
        raise ValueError("non-executable searchBase/searchRoute")
    url = base.rstrip("/") + "/" + route.lstrip("/")

    spec = plan.get("searchRequestSpec") if isinstance(plan.get("searchRequestSpec"), dict) else {}
    method = text(spec.get("method") or "GET", 12).upper()
    if method not in {"GET", "POST", "PUT", "PATCH"}:
        method = "GET"
    headers = {
        str(k): text(v, 500)
        for k, v in (spec.get("headers") or {}).items()
        if str(k).casefold() in SAFE_HEADERS and text(v, 500)
    }
    headers.setdefault("User-Agent", "Mozilla/5.0 NiakVIO-IdentityShape/1")
    headers.setdefault("Accept", "application/json,text/plain,*/*")

    values = {"query": query, "title": query, "q": query}
    body: bytes | None = None
    body_kind = text(spec.get("bodyKind"), 20).casefold()
    raw_body = expand_object(spec.get("body"), values)
    if body_kind == "json" and isinstance(raw_body, dict):
        body = json.dumps(raw_body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        headers.setdefault("Content-Type", "application/json")
    elif body_kind == "form" and isinstance(raw_body, dict):
        body = urllib.parse.urlencode({str(k): str(v) for k, v in raw_body.items()}).encode("utf-8")
        headers.setdefault("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8")

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        status = int(getattr(response, "status", 200) or 200)
        content_type = text(response.headers.get("content-type"), 160).casefold()
        payload = response.read(262144)
    return status, content_type, payload


def inspect_payload(payload: bytes, content_type: str, expected: str) -> dict[str, Any]:
    raw = payload.decode("utf-8", errors="replace").lstrip("\ufeff\r\n\t ")
    parsed: Any = None
    parse_error = ""
    if "json" in content_type or raw.startswith(("{", "[")):
        try:
            parsed = json.loads(raw)
        except Exception as exc:  # diagnostic only
            parse_error = type(exc).__name__
    result: dict[str, Any] = {
        "payloadBytes": len(payload),
        "jsonParsed": parsed is not None,
        "jsonRootType": type(parsed).__name__ if parsed is not None else "",
        "parseError": parse_error,
        "topLevelKeys": sorted(parsed.keys())[:32] if isinstance(parsed, dict) else [],
        "rowCount": 0,
        "candidateRows": [],
        "bestScore": 0,
        "bestIdentityField": "",
        "bestIdentityValue": "",
        "bestLabelField": "",
        "bestLabelValue": "",
    }
    if parsed is None:
        return result

    rows = json_rows(parsed, [])
    result["rowCount"] = len(rows)
    candidates: list[dict[str, Any]] = []
    for index, row in enumerate(rows[:120]):
        labels = []
        for field in LABEL_FIELDS:
            value = text(row.get(field))
            if value:
                labels.append({"field": field, "value": value, "score": title_score(value, expected)})
        labels.sort(key=lambda item: int(item["score"]), reverse=True)
        identities = []
        for field in ID_FIELDS:
            value = text(row.get(field), 160)
            if value and SAFE_ID_RE.fullmatch(value):
                identities.append({"field": field, "value": value})
        best = int(labels[0]["score"]) if labels else 0
        if labels or identities:
            candidates.append({
                "rowIndex": index,
                "keys": sorted(str(key) for key in row.keys())[:32],
                "bestScore": best,
                "labels": labels[:6],
                "identities": identities[:6],
            })
        if best > int(result["bestScore"]):
            result["bestScore"] = best
            if labels:
                result["bestLabelField"] = labels[0]["field"]
                result["bestLabelValue"] = labels[0]["value"]
            if identities:
                result["bestIdentityField"] = identities[0]["field"]
                result["bestIdentityValue"] = identities[0]["value"]
    result["candidateRows"] = candidates[:12]
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", action="append", required=True)
    parser.add_argument("--timeout", type=float, default=12.0)
    args = parser.parse_args()

    overrides = load(OVERRIDES)
    patches = overrides.get("provider_patches") if isinstance(overrides, dict) else {}
    yield_report = load(YIELD) if YIELD.is_file() else {"rows": []}
    task_rows = yield_report.get("rows") if isinstance(yield_report, dict) else []
    output: dict[str, Any] = {"schemaVersion": 1, "providers": []}

    for raw_provider in args.provider:
        provider = cid(raw_provider)
        patch = patches.get(provider) if isinstance(patches, dict) and isinstance(patches.get(provider), dict) else {}
        plans = patch.get("provider_value_plan") if isinstance(patch.get("provider_value_plan"), list) else []
        provider_out = {"providerId": provider, "planCount": len(plans), "probes": []}
        rows = [
            row for row in task_rows or []
            if isinstance(row, dict) and cid(row.get("provider_id")) == provider and text(row.get("fixture_title"))
        ]
        seen: set[tuple[str, str]] = set()
        for row in rows:
            semantic = text(row.get("semantic_type"), 20).casefold()
            expected = text(row.get("fixture_title"), 180)
            for plan_index, plan in enumerate(plans[:12]):
                if not isinstance(plan, dict):
                    continue
                lanes = [text(v, 20).casefold() for v in plan.get("semanticTypes") or []]
                if lanes and semantic not in lanes and not (semantic == "anime" and "tv" in lanes):
                    continue
                key = (semantic, expected)
                if key in seen:
                    continue
                seen.add(key)
                probe: dict[str, Any] = {
                    "planIndex": plan_index,
                    "semanticType": semantic,
                    "expectedTitle": expected,
                    "searchBaseHost": urllib.parse.urlsplit(text(plan.get("searchBase"), 500)).hostname or "",
                    "searchRouteShape": re.sub(r"=[^&#{}]+", "=<value>", text(plan.get("searchRoute"), 1000)),
                }
                try:
                    status, content_type, payload = request(plan, expected, args.timeout)
                    probe["status"] = status
                    probe["contentType"] = content_type
                    probe.update(inspect_payload(payload, content_type, expected))
                except urllib.error.HTTPError as exc:
                    probe.update({"status": int(exc.code), "error": "HTTPError"})
                except Exception as exc:  # diagnostic only
                    probe.update({"status": 0, "error": type(exc).__name__})
                provider_out["probes"].append(probe)
                print(
                    "FIELD_PROVIDER_VALUE_IDENTITY_SHAPE "
                    f"provider={provider} semantic={semantic} status={probe.get('status', 0)} "
                    f"json={str(probe.get('jsonParsed', False)).lower()} rows={probe.get('rowCount', 0)} "
                    f"best_score={probe.get('bestScore', 0)} "
                    f"identity_field={probe.get('bestIdentityField') or '-'} "
                    f"identity={probe.get('bestIdentityValue') or '-'}",
                    flush=True,
                )
        output["providers"].append(provider_out)

    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"FIELD_PROVIDER_VALUE_IDENTITY_SHAPE_REPORT path={OUTPUT.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
