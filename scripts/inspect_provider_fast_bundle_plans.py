#!/usr/bin/env python3
"""Inspect targeted materialized bundles for structured repair-plan projection.

Diagnostic only. This does not alter provider DATA or publication state.
Besides plan projection, print bounded control-flow excerpts from the exact bundle
that the targeted Nuvio probe executes. This prevents reasoning from an abstract
ProviderBase source when a materializer/wrapper has changed call ownership.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
OVERRIDES = ROOT / "provider-overrides.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def compact(value: str, limit: int = 900) -> str:
    row = re.sub(r"\s+", " ", value).strip()
    return row[:limit] + ("…" if len(row) > limit else "")


def function_excerpt(text: str, name: str, limit: int = 1400) -> str:
    # Bounded brace walk from the exact named function. It need not be a JS
    # parser; this is diagnostics only and intentionally never mutates code.
    match = re.search(rf"(?:async\s+)?function\s+{re.escape(name)}\s*\([^)]*\)\s*\{{", text)
    if not match:
        return "<missing>"
    start = match.start()
    brace = text.find("{", match.start(), match.end())
    depth = 0
    quote = ""
    escaped = False
    end = min(len(text), start + 12000)
    for index in range(brace, end):
        ch = text[index]
        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = ""
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return compact(text[start:index + 1], limit)
    return compact(text[start:start + limit], limit)


def marker_pos(text: str, needle: str) -> int:
    return text.find(needle)


def terminal_excerpt(text: str) -> str:
    candidates = []
    for pattern in (
        r"getStreams\s*:\s*[^,}\n]+",
        r"getStreams\s*=\s*[^;\n]+",
        r"exports\.[A-Za-z0-9_]*getStreams[^;\n]*",
        r"return\s+await\s+_spv4GetStreams\([^;]+;",
        r"return\s+_spv4GetStreams\([^;]+;",
    ):
        for match in re.finditer(pattern, text):
            candidates.append((match.start(), match.group(0)))
    if not candidates:
        return "<no-terminal-pattern>"
    # The last ownership assignment/call is normally closest to the exported
    # terminal wrapper. Print up to the last three for context.
    candidates.sort()
    return " || ".join(compact(value, 350) for _, value in candidates[-3:])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", action="append", required=True)
    args = parser.parse_args()

    manifest = load(MANIFEST)
    rows = {
        cid(row.get("id")): row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and cid(row.get("id"))
    }
    overrides = load(OVERRIDES)
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    failed: list[str] = []

    for raw in args.provider:
        provider = cid(raw)
        row = rows.get(provider) or {}
        patch = patches.get(provider) if isinstance(patches.get(provider), dict) else {}
        filename = str(row.get("filename") or "")
        path = ROOT / filename
        if not filename or not path.exists():
            failed.append(provider + ":bundle-missing")
            continue
        text = path.read_text(encoding="utf-8")
        plans = patch.get("search_request_plan") if isinstance(patch.get("search_request_plan"), list) else []
        expected_bases = [str(plan.get("base") or "").strip() for plan in plans if isinstance(plan, dict) and str(plan.get("base") or "").strip()]
        marker = '"searchRequestPlan"' in text
        projected_bases = [base for base in expected_bases if base in text]
        print(
            "FIELD_PROVIDER_FAST_BUNDLE_PLAN "
            f"provider={provider} file={filename} expected_search_plan={len(plans)} "
            f"marker={str(marker).lower()} projected_bases={len(projected_bases)}/{len(expected_bases)} "
            f"bases={','.join(expected_bases)}",
            flush=True,
        )
        positions = {
            "v16": marker_pos(text, "NIAKVIO_PROVIDER_EXECUTION_AUTHORITY_V16"),
            "recipe": marker_pos(text, "_resolveApiRecipe(proofMeta"),
            "search": marker_pos(text, "_resolveSearchRequestPlan(proofMeta"),
            "family": marker_pos(text, 'if (family === "stremio-json")'),
            "generic": marker_pos(text, "await getStreams(tmdbId"),
        }
        print(
            "FIELD_PROVIDER_FAST_CONTROL_ORDER "
            f"provider={provider} " + " ".join(f"{key}={value}" for key, value in positions.items()),
            flush=True,
        )
        print(f"FIELD_PROVIDER_FAST_TERMINAL provider={provider} code={terminal_excerpt(text)}", flush=True)
        for name in ("getStreams", "_spv4GetStreams", "_resolveSearchRequestPlan", "_resolveApiRecipe", "_substituteDomain"):
            print(
                f"FIELD_PROVIDER_FAST_FUNCTION provider={provider} name={name} code={function_excerpt(text, name)}",
                flush=True,
            )
        if plans and (not marker or len(projected_bases) != len(expected_bases)):
            failed.append(provider + ":search-plan-not-projected")
        if positions["v16"] >= 0:
            ordered = [positions["recipe"], positions["search"], positions["family"]]
            if all(value >= 0 for value in ordered) and ordered != sorted(ordered):
                failed.append(provider + ":v16-authority-order-invalid")

    if failed:
        raise SystemExit("materialized structured-plan/control-flow projection failed: " + ",".join(failed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
