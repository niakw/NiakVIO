#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

FIXTURES = {
    "interstellar": "movie",
    "breaking-bad-s01e01": "tv",
    "jujutsu-kaisen-s01e01": "anime",
}
RUNS = {
    "tv": "34587026051 (NuvioTV audited ref 23d1fe478e380860dae3eb41c8770533361a0cc5)",
    "desktop-macos": "34585968905",
    "desktop-windows": "34585968905",
    "mobile-android": "34585969062",
    "mobile-ios": "34585968903",
}
KV_RE = re.compile(r"([A-Za-z0-9_]+)=([^ ]*)")


def norm(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").casefold())


def clean_url(value: object) -> str:
    return str(value or "").strip().rstrip("/").casefold()


def b64decode_text(value: str) -> str:
    try:
        padded = value + "=" * ((4 - len(value) % 4) % 4)
        return base64.urlsafe_b64decode(padded.encode()).decode("utf-8", errors="replace")
    except Exception:
        return value


def manifest_rows(path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows: dict[str, dict[str, Any]] = {}
    aliases: dict[str, str] = {}
    for row in data.get("scrapers", []):
        if not isinstance(row, dict):
            continue
        pid = str(row.get("id") or "").strip()
        if not pid:
            continue
        types = row.get("canonicalSupportedTypes")
        if not isinstance(types, list) or not types:
            types = [v for v in row.get("supportedTypes", []) if str(v).lower() in {"movie", "tv", "anime"}]
        canonical_types: list[str] = []
        for raw in types:
            typ = str(raw or "").strip().lower()
            if typ == "series":
                typ = "tv"
            if typ in {"movie", "tv", "anime"} and typ not in canonical_types:
                canonical_types.append(typ)
        item = dict(row)
        item["canonical_types"] = canonical_types
        rows[pid.casefold()] = item
        aliases[norm(pid)] = pid.casefold()
        for raw in row.get("aliases", []) if isinstance(row.get("aliases"), list) else []:
            aliases.setdefault(norm(raw), pid.casefold())
    return rows, aliases


def registry_rows(path: Path) -> list[tuple[str, dict[str, Any]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    root = data.get("providers", data)
    if not isinstance(root, dict):
        raise SystemExit("provider-hubs.json: expected object/provider mapping")
    out = []
    for pid, cfg in root.items():
        if not isinstance(cfg, dict):
            continue
        hub = str(cfg.get("hub") or "").strip()
        if hub:
            out.append((str(pid), cfg))
    if len(out) != 46:
        raise SystemExit(f"provider-hubs invariant failed: expected 46 non-null hubs, got {len(out)}")
    return out


def overrides(path: Path) -> dict[str, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    root = data.get("provider_patches", {})
    return {str(k).casefold(): v for k, v in root.items() if isinstance(v, dict)}


def registry_aliases(pid: str, cfg: dict[str, Any]) -> list[str]:
    values: list[str] = [pid]
    for key in ("id", "provider", "providerId", "provider_id", "manifestId", "manifest_id", "canonicalId", "canonical_id"):
        if cfg.get(key):
            values.append(str(cfg[key]))
    for key in ("aliases", "providerAliases", "provider_aliases"):
        raw = cfg.get(key)
        if isinstance(raw, list):
            values.extend(str(v) for v in raw if v)
    return values


def match_manifest(pid: str, cfg: dict[str, Any], manifest: dict[str, dict[str, Any]], aliases: dict[str, str]) -> str | None:
    direct = pid.casefold()
    if direct in manifest:
        return direct
    for value in registry_aliases(pid, cfg):
        key = aliases.get(norm(value))
        if key in manifest:
            return key
    # Conservative normalized exact match only; never fuzzy-match two unrelated providers.
    target = norm(pid)
    matches = [key for key in manifest if norm(key) == target]
    return matches[0] if len(matches) == 1 else None


def parse_native_logs(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "platform_valid": True,
        "platform_notes": [],
        "fixtures": defaultdict(lambda: defaultdict(lambda: {
            "result": None,
            "error": [],
            "skipped": False,
            "players": [],
            "transports": [],
        })),
    }
    logs = list(root.rglob("*corpus*.log")) if root.exists() else []
    for path in logs:
        text = path.read_text(encoding="utf-8", errors="replace")
        if "FIELD_NATIVE_UI_LAUNCH_ERROR" in text:
            result["platform_valid"] = False
            result["platform_notes"].append("client UI launch failed")
        for line in text.splitlines():
            if "FIELD_NATIVE_" not in line:
                continue
            kv = dict(KV_RE.findall(line))
            fixture = kv.get("fixture", "")
            if fixture not in FIXTURES:
                continue
            provider64 = kv.get("provider64", "")
            if not provider64:
                continue
            provider = b64decode_text(provider64).casefold()
            cell = result["fixtures"][fixture][provider]
            if "FIELD_NATIVE_RESULT " in line:
                try:
                    cell["result"] = int(kv.get("count", "0"))
                except ValueError:
                    cell["result"] = 0
            elif "FIELD_NATIVE_ERROR " in line:
                cell["error"].append(b64decode_text(kv.get("error64", "")))
            elif "FIELD_NATIVE_PROVIDER_SKIPPED " in line:
                cell["skipped"] = True
            elif "FIELD_NATIVE_PLAYER " in line:
                try:
                    duration = float(kv.get("duration_seconds", "0") or 0)
                except ValueError:
                    duration = 0.0
                cell["players"].append({
                    "state": kv.get("state", ""),
                    "failure_stage": kv.get("failure_stage", ""),
                    "duration": duration,
                })
            elif "FIELD_NATIVE_TRANSPORT " in line:
                try:
                    duration = float(kv.get("duration_seconds", "0") or 0)
                except ValueError:
                    duration = 0.0
                cell["transports"].append({
                    "state": kv.get("state", ""),
                    "kind": kv.get("kind", ""),
                    "status": kv.get("status", ""),
                    "duration": duration,
                })
    # Brain files are the authoritative completeness flag when present.
    brains = list(root.rglob("*brain.json")) if root.exists() else []
    for path in brains:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if data.get("evidenceComplete") is False:
            result["platform_valid"] = False
            result["platform_notes"].append(f"incomplete evidence: {path.name}")
    return result


def parse_ios(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "platform_valid": True,
        "platform_notes": [],
        "fixtures": defaultdict(lambda: defaultdict(lambda: {
            "result": None,
            "error": [],
            "skipped": False,
            "players": [],
            "transports": [],
        })),
    }
    for path in root.rglob("*corpus*.log") if root.exists() else []:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            marker = "FIELD_NATIVE_IOS_RESULT "
            if marker not in line:
                continue
            try:
                row = json.loads(line.split(marker, 1)[1])
            except Exception:
                continue
            fixture = str(row.get("fixture") or "")
            if fixture not in FIXTURES:
                continue
            provider = str(row.get("provider") or "").casefold()
            if not provider:
                continue
            cell = result["fixtures"][fixture][provider]
            state = str(row.get("state") or "")
            if state == "timeout":
                cell["error"].append("timeout")
            try:
                cell["result"] = int(row.get("count") or 0)
            except Exception:
                cell["result"] = 0
    for path in root.rglob("*brain.json") if root.exists() else []:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if data.get("evidenceComplete") is False:
            result["platform_valid"] = False
            result["platform_notes"].append(f"incomplete evidence: {path.name}")
    return result


def fixture_cell(platform: dict[str, Any], provider: str | None, fixture: str, capability: bool, *, tv_integrity: bool = False) -> tuple[str, dict[str, Any]]:
    if not capability:
        return "⚪ N/A", {}
    if not platform.get("platform_valid", True):
        notes = "; ".join(sorted(set(platform.get("platform_notes") or []))) or "incomplete Lab evidence"
        return f"🟣 invalid Lab ({notes})", {}
    if not provider:
        return "🟣 unmapped provider", {}
    cell = platform["fixtures"].get(fixture, {}).get(provider.casefold())
    if not cell:
        return "🟣 no observation", {}
    if cell.get("error"):
        return "🔴 " + ", ".join(cell["error"][:2]), cell
    if cell.get("skipped") and cell.get("result") is None:
        return "🟣 skipped despite declared capability", cell
    count = cell.get("result")
    if not count:
        return "🔴 0 stream", cell
    if tv_integrity:
        players = cell.get("players") or []
        transports = cell.get("transports") or []
        ready = [row for row in players if row.get("state") == "ready"]
        short = [row for row in players if row.get("state") == "short_media"]
        transport_ok = [row for row in transports if row.get("state") == "ok"]
        if ready and transport_ok:
            return f"🟢 {count} stream(s), player ready + transport OK", cell
        if short:
            durations = ",".join(f"{row.get('duration', 0):.1f}s" for row in short[:3])
            return f"🔴 false positive: short_media {durations}", cell
        if ready and not transport_ok:
            dead = ",".join(str(row.get("status") or row.get("state")) for row in transports[:3])
            return f"🟠 {count} raw, player ready mais transport KO ({dead})", cell
        if players or transports:
            pstate = ",".join(str(row.get("state")) for row in players[:3]) or "none"
            tstate = ",".join(f"{row.get('state')}:{row.get('status')}" for row in transports[:3]) or "none"
            return f"🔴 {count} raw, playback KO player={pstate} transport={tstate}", cell
        return f"🟠 {count} raw stream(s), playback non prouvé", cell
    return f"🟢 {count} raw stream(s)", cell


def markdown_escape(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--tv", required=True)
    parser.add_argument("--macos", required=True)
    parser.add_argument("--windows", required=True)
    parser.add_argument("--android", required=True)
    parser.add_argument("--ios", required=True)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    registry = registry_rows(root / "provider-hubs.json")
    manifest, manifest_aliases = manifest_rows(root / "manifest.json")
    patches = overrides(root / "provider-overrides.json")
    evidence = {
        "tv": parse_native_logs(Path(args.tv)),
        "desktop-macos": parse_native_logs(Path(args.macos)),
        "desktop-windows": parse_native_logs(Path(args.windows)),
        "mobile-android": parse_native_logs(Path(args.android)),
        "mobile-ios": parse_ios(Path(args.ios)),
    }

    rows = []
    for registry_id, cfg in registry:
        canonical = match_manifest(registry_id, cfg, manifest, manifest_aliases)
        mrow = manifest.get(canonical or "", {})
        patch = patches.get((canonical or registry_id).casefold(), patches.get(registry_id.casefold(), {}))
        hub = str(cfg.get("hub") or "").strip()
        official = str(patch.get("official_hub") or "").strip()
        if official and clean_url(official) == clean_url(hub):
            hub_relation = "match"
        elif official:
            hub_relation = "conflict"
        else:
            hub_relation = "registry-only"
        caps = list(mrow.get("canonical_types") or [])
        cells: dict[str, dict[str, str]] = {}
        for fixture, lane in FIXTURES.items():
            cells[fixture] = {}
            for platform_name, platform in evidence.items():
                label, _ = fixture_cell(
                    platform,
                    canonical,
                    fixture,
                    lane in caps,
                    tv_integrity=(platform_name == "tv"),
                )
                cells[fixture][platform_name] = label

        tv_labels = [cells[f]["tv"] for f in FIXTURES if FIXTURES[f] in caps]
        any_tv_green = any(label.startswith("🟢") for label in tv_labels)
        any_tv_orange = any(label.startswith("🟠") for label in tv_labels)
        all_tv_na = not tv_labels
        desktop_labels = [cells[f][p] for f in FIXTURES for p in ("desktop-macos", "desktop-windows") if FIXTURES[f] in caps]
        ios_labels = [cells[f]["mobile-ios"] for f in FIXTURES if FIXTURES[f] in caps]
        desktop_has_red = any(label.startswith("🔴") for label in desktop_labels)
        ios_has_red = any(label.startswith("🔴") for label in ios_labels)

        if not canonical:
            overall = "🟣 hub non mappé au manifest"
            cause = "registry id/aliases ne correspondent à aucun des 96 providers publiés"
            repair = "réconcilier l’identité du registre sans inventer d’alias"
        elif any_tv_green and (desktop_has_red or ios_has_red):
            overall = "🟠 provider prouvé TV, divergence runtime"
            cause = "le provider/route fonctionne sur NuvioTV audité mais échoue ou retourne 0 sur Desktop/iOS"
            repair = "corriger le contrat runtime commun avant toute réparation provider spécifique"
        elif any_tv_green:
            overall = "🟢 provider prouvé TV"
            cause = "au moins une lane produit un média lisible et un transport valide"
            repair = "préserver la route prouvée; traiter uniquement les lanes rouges restantes"
        elif any_tv_orange:
            overall = "🟠 sortie brute non jouable"
            cause = "des streams sont retournés mais la preuve lecteur/transport échoue"
            repair = "réparer transport/headers/identité; ne pas compter la sortie brute comme succès"
        elif all_tv_na:
            overall = "⚪ aucune lane TV applicable"
            cause = "aucune capacité canonique correspondante"
            repair = "audit identité/capacités"
        else:
            overall = "🔴 aucune lane TV jouable prouvée"
            cause = "0 stream, timeout, faux média ou transport non jouable sur les lanes déclarées"
            repair = "réparer route/identité selon la première cause prouvée; conserver force-ON catalogue"

        # Hard evidence override: Allwish's two identical short Telegram media are not valid content.
        if canonical and norm(canonical) == norm("ALLWISH"):
            overall = "🔴 faux positifs d’identité"
            cause = "Interstellar et Breaking Bad renvoient les mêmes MP4 ~33s/~23s; lecteur=short_media, failure_stage=duration_identity"
            repair = "fail-closed après échec route canonique; interdire média social/générique comme preuve d’œuvre; test cross-fixture"

        if hub_relation == "conflict":
            repair += "; réconcilier hub registre vs official_hub sans écraser arbitrairement le hub prouvé"

        rows.append({
            "registryId": registry_id,
            "manifestId": mrow.get("id") if canonical else None,
            "hub": hub,
            "officialHub": official or None,
            "hubRelation": hub_relation,
            "capabilities": caps,
            "cells": cells,
            "overall": overall,
            "cause": cause,
            "repair": repair,
        })

    assert len(rows) == 46
    summary = {
        "schemaVersion": 1,
        "hubCount": len(rows),
        "runs": RUNS,
        "platformEvidence": {
            key: {
                "valid": bool(value.get("platform_valid", True)),
                "notes": sorted(set(value.get("platform_notes") or [])),
            }
            for key, value in evidence.items()
        },
        "rows": rows,
    }
    Path(args.output_json).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = [
        "# Matrice des 46 hubs NiakVIO — preuves Labs natives",
        "",
        "> Générée automatiquement depuis `provider-hubs.json`, `provider-overrides.json`, `manifest.json` et les artefacts Labs exacts. Un `count > 0` n’est **jamais** considéré comme un succès TV si le lecteur ou le transport échoue.",
        "",
        f"- Hubs non nuls étudiés : **{len(rows)}/46**.",
        f"- TV : run **{RUNS['tv']}** — preuve runtime sur le ref NuvioTV audité, car le HEAD officiel était cassé avant compilation.",
        f"- Desktop macOS/Windows : run **{RUNS['desktop-macos']}**.",
        f"- Android Mobile : run **{RUNS['mobile-android']}** — evidence invalide si le launcher officiel n’a pas pu démarrer.",
        f"- iOS : run **{RUNS['mobile-ios']}** — exécution/matrice exhaustive complète; un workflow vert ne signifie pas que les providers ont produit des streams.",
        "",
        "Légende : 🟢 média/transport prouvé ; 🟠 partiel ou divergence ; 🔴 cassé/faux positif ; 🟣 preuve invalide/incomplète ; ⚪ non applicable.",
        "",
        "| Registre | Manifest | Hub registre | official_hub | Relation | Capacités | TV film | TV série | TV anime | Desktop macOS | Desktop Windows | Android Mobile | iOS | Verdict | Cause / réparation |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        caps = ", ".join(row["capabilities"]) or "—"
        movie = row["cells"]["interstellar"]
        tv = row["cells"]["breaking-bad-s01e01"]
        anime = row["cells"]["jujutsu-kaisen-s01e01"]
        def merge_platform(platform: str) -> str:
            vals = []
            for fixture, lane in FIXTURES.items():
                if lane in row["capabilities"]:
                    vals.append(f"{lane}:{row['cells'][fixture][platform]}")
            return " / ".join(vals) or "⚪ N/A"
        md.append("| " + " | ".join(markdown_escape(v) for v in [
            row["registryId"],
            row["manifestId"] or "—",
            row["hub"],
            row["officialHub"] or "—",
            row["hubRelation"],
            caps,
            movie["tv"],
            tv["tv"],
            anime["tv"],
            merge_platform("desktop-macos"),
            merge_platform("desktop-windows"),
            merge_platform("mobile-android"),
            merge_platform("mobile-ios"),
            row["overall"],
            row["cause"] + " → " + row["repair"],
        ]) + " |")

    md.extend([
        "",
        "## Règles d’interprétation",
        "",
        "Le registre de hubs est un périmètre d’audit et de découverte, **pas un gate d’activation**. La politique de publication reste 96/96 ON. Les états repair/off/quarantine restent diagnostiques et ne doivent pas écrire `enabled:false`.",
        "",
        "Android Mobile de ce run n’est pas utilisable pour déclarer un provider rouge si l’UI n’a pas pu être lancée. Les cellules sont donc 🟣 au lieu de transformer un défaut de harness en défaut provider.",
        "",
        "Allwish est explicitement rejeté malgré `count=2` : les mêmes deux médias très courts sont observés sur des œuvres différentes et le lecteur les classe `short_media`/`duration_identity`.",
        "",
    ])
    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")
    print(f"HUB_LAB_MATRIX_OK hubs={len(rows)} output={args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
