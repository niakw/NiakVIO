#!/usr/bin/env python3
"""Merge native-reader evidence and render the README provider matrix.

The visible inventory is derived from enabled scrapers in the general manifest,
so it cannot silently drift from the plugin users actually load. Native-reader
proofs are crossed onto that inventory as they arrive; missing proof stays unknown
rather than being misreported as a provider failure.
"""
from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- NIAKVIO_PROVIDER_RESULTS_START -->"
END = "<!-- NIAKVIO_PROVIDER_RESULTS_END -->"
DEVICES = (
    ("tv", "TV"),
    ("mobile", "Mobile"),
    ("desktop_macos", "Desktop macOS"),
    ("desktop_windows", "Desktop Windows"),
)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def iso_date(value: str | None) -> str:
    raw = str(value or "").strip()
    if not raw:
        return datetime.now(timezone.utc).date().isoformat()
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return raw[:10]


def normalize_device(client: str) -> str | None:
    value = str(client or "").strip().casefold()
    if not value:
        return None
    if "tv" in value:
        return "tv"
    if "mobile" in value:
        return "mobile"
    if "mac" in value:
        return "desktop_macos"
    if "windows" in value or value.endswith("-win") or value == "win":
        return "desktop_windows"
    if "desktop" in value:
        return "desktop_macos" if "darwin" in value else "desktop_windows" if "win" in value else None
    return None


def fixture_catalog(results: dict[str, Any]) -> dict[str, dict[str, Any]]:
    fixtures = dict(results.get("fixtures") or {})
    corpus = load_json(ROOT / "engine_v2" / "config" / "native-corpus.json", {})
    for row in corpus.get("fixtures") or []:
        if not isinstance(row, dict) or not row.get("id"):
            continue
        fixture_id = str(row["id"])
        label = str(row.get("title") or fixture_id)
        season = row.get("season")
        episode = row.get("episode")
        if season is not None and episode is not None:
            label += f" S{int(season):02d}E{int(episode):02d}"
        fixtures.setdefault(
            fixture_id,
            {"label": label, "mediaType": str(row.get("mediaType") or "unknown")},
        )
    return fixtures


def proof_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("provider") or "").strip().casefold(),
        str(row.get("fixture") or "").strip(),
        str(row.get("mediaType") or "").strip().casefold(),
    )


def merge_diagnostics(results: dict[str, Any], diagnostics_root: Path, run_id: str) -> bool:
    fixtures = fixture_catalog(results)
    results["fixtures"] = fixtures
    proofs = [row for row in (results.get("proofs") or []) if isinstance(row, dict)]
    by_key = {proof_key(row): row for row in proofs}
    changed = False

    for path in sorted(diagnostics_root.rglob("*brain.json")) if diagnostics_root.exists() else []:
        payload = load_json(path, {})
        if payload.get("evidenceComplete") is not True:
            continue
        verified_at = iso_date(payload.get("generatedAt"))
        for obs in payload.get("observations") or []:
            if not isinstance(obs, dict):
                continue
            if obs.get("observationLayer") != "player" or obs.get("failureClass") != "healthy":
                continue
            if str(obs.get("routeMode") or "declared").casefold() == "capability_probe":
                continue
            provider = str(obs.get("provider") or "").strip().casefold()
            fixture = str(obs.get("fixture") or "").strip()
            media_type = str(obs.get("requestType") or "unknown").strip().casefold()
            device = normalize_device(str(obs.get("client") or ""))
            if not provider or not fixture or not device:
                continue
            key = (provider, fixture, media_type)
            row = by_key.get(key)
            if row is None:
                row = {
                    "provider": provider,
                    "fixture": fixture,
                    "mediaType": media_type,
                    "devices": {},
                }
                proofs.append(row)
                by_key[key] = row
                changed = True
            devices = row.setdefault("devices", {})
            current = devices.get(device) if isinstance(devices, dict) else None
            candidate = {
                "verifiedAt": verified_at,
                "runId": str(run_id),
                "source": "official-native-reader",
            }
            if not isinstance(current, dict) or str(current.get("verifiedAt") or "") <= verified_at:
                if current != candidate:
                    devices[device] = candidate
                    changed = True
            fixtures.setdefault(
                fixture,
                {"label": fixture.replace("-", " ").title(), "mediaType": media_type},
            )

    proofs.sort(key=lambda row: (str(row.get("fixture")), str(row.get("provider"))))
    results["proofs"] = proofs
    if changed:
        latest = max(
            (
                str(proof.get("verifiedAt") or "")
                for row in proofs
                for proof in (row.get("devices") or {}).values()
                if isinstance(proof, dict)
            ),
            default=results.get("updatedAt") or datetime.now(timezone.utc).date().isoformat(),
        )
        results["updatedAt"] = latest
    return changed


def media_label(value: str) -> str:
    return {"movie": "Film", "tv": "Série", "anime": "Anime"}.get(str(value).casefold(), str(value).title())


def active_providers() -> list[dict[str, Any]]:
    manifest = load_json(ROOT / "manifest.json", {})
    logo_index = load_json(ROOT / "assets" / "providers" / "index.json", {})
    branding_index = load_json(ROOT / "assets" / "providers" / "emojis.json", {})
    indexed = logo_index.get("providers") if isinstance(logo_index, dict) else {}
    branding = branding_index.get("providers") if isinstance(branding_index, dict) else {}
    if not isinstance(indexed, dict):
        indexed = {}
    if not isinstance(branding, dict):
        branding = {}
    rows: list[dict[str, Any]] = []
    for scraper in manifest.get("scrapers") or []:
        if not isinstance(scraper, dict) or scraper.get("enabled") is not True:
            continue
        provider_id = str(scraper.get("id") or "").strip()
        if not provider_id:
            continue
        key = provider_id.casefold()
        local = indexed.get(key)
        brand = branding.get(key)
        clean_name = (
            str(brand.get("name") or "").strip()
            if isinstance(brand, dict)
            else ""
        ) or str(scraper.get("name") or provider_id).strip()
        logo = ""
        if isinstance(local, dict):
            urls = local.get("urls") or {}
            if isinstance(urls, dict):
                logo = str(urls.get("72x32") or urls.get("96x40") or "").strip()
        if not logo:
            logo = str(scraper.get("logo") or "").strip()
        rows.append(
            {
                "id": provider_id,
                "key": key,
                "name": clean_name,
                "logo": logo,
                "types": [str(value) for value in (scraper.get("supportedTypes") or []) if str(value).strip()],
            }
        )
    return rows


def provider_proof_summary(
    provider: dict[str, Any], results: dict[str, Any], fixtures: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    matching = [
        row
        for row in (results.get("proofs") or [])
        if isinstance(row, dict) and str(row.get("provider") or "").strip().casefold() == provider["key"]
    ]
    devices: dict[str, str] = {}
    verified_content: list[str] = []
    seen_content: set[str] = set()
    for row in matching:
        fixture = str(row.get("fixture") or "").strip()
        fixture_row = fixtures.get(fixture) if isinstance(fixtures.get(fixture), dict) else {}
        label = str(fixture_row.get("label") or fixture.replace("-", " ").title())
        kind = media_label(str(row.get("mediaType") or fixture_row.get("mediaType") or "unknown"))
        content = f"{label} ({kind})" if label else kind
        if content not in seen_content:
            seen_content.add(content)
            verified_content.append(content)
        for device, proof in (row.get("devices") or {}).items():
            if not isinstance(proof, dict):
                continue
            date = str(proof.get("verifiedAt") or "")
            if date and date >= devices.get(str(device), ""):
                devices[str(device)] = date
    return {
        "proofCount": len(matching),
        "content": verified_content,
        "devices": devices,
        "latest": max(devices.values(), default="—"),
    }


def device_cell(summary: dict[str, Any], device: str) -> str:
    date = str((summary.get("devices") or {}).get(device) or "")
    return f"✅ {date}" if date else "—"


def provider_label(provider: dict[str, Any]) -> str:
    name = html.escape(str(provider.get("name") or provider.get("id") or ""), quote=False).replace("|", "&#124;")
    logo = html.escape(str(provider.get("logo") or ""), quote=True)
    if not logo:
        return name
    return f'<img src="{logo}" width="36" alt="">&nbsp; {name}'


def render(results: dict[str, Any]) -> str:
    fixtures = fixture_catalog(results)
    providers = active_providers()
    summaries = {provider["key"]: provider_proof_summary(provider, results, fixtures) for provider in providers}
    positive_dates = [
        str(summary.get("latest"))
        for summary in summaries.values()
        if str(summary.get("latest") or "") not in ("", "—")
    ]
    last_update = str(results.get("updatedAt") or max(positive_dates, default="—"))
    lines = [
        START,
        "## Providers actifs & résultats natifs vérifiés",
        "",
        f"**Inventaire : {len(providers)} providers activés dans `manifest.json`. Dernière preuve positive : {last_update}.**",
        "",
        "La liste ci-dessous est reconstruite automatiquement depuis le **manifest général actif**. Les résultats du Deep/Brain et des Labs natifs sont ensuite croisés dessus. Une case `—` signifie uniquement *pas encore de preuve positive conservée* ; elle n'est jamais transformée automatiquement en échec.",
        "",
        "| Provider | Types déclarés | Contenus réellement vérifiés | TV | Mobile | Desktop macOS | Desktop Windows | Preuves | Dernière preuve |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for provider in providers:
        summary = summaries[provider["key"]]
        types = ", ".join(media_label(value) for value in provider.get("types") or []) or "—"
        contents = "<br>".join(str(value).replace("|", "\\|") for value in summary.get("content") or []) or "—"
        lines.append(
            "| {provider} | {types} | {contents} | {tv} | {mobile} | {mac} | {win} | {proofs} | {date} |".format(
                provider=provider_label(provider),
                types=types,
                contents=contents,
                tv=device_cell(summary, "tv"),
                mobile=device_cell(summary, "mobile"),
                mac=device_cell(summary, "desktop_macos"),
                win=device_cell(summary, "desktop_windows"),
                proofs=summary.get("proofCount") or "—",
                date=summary.get("latest") or "—",
            )
        )
    lines.extend(
        [
            "",
            "### Ce que NiakVIO ajoute à une simple liste de providers",
            "",
            "| Capacité | NiakVIO | Manifest/provider brut |",
            "|---|---|---|",
            "| Inventaire automatiquement synchronisé au manifest actif | ✅ | N/A |",
            "| Plusieurs upstreams comparés | ✅ | Généralement une seule source |",
            "| Preuve lecteur officielle par device | ✅ TV / Mobile / Desktop | Non garantie |",
            "| Vérification œuvre / saison / épisode | ✅ | Non garantie |",
            "| Validation média et premier segment | ✅ | Non garantie |",
            "| Repair Brain + retest après mutation | ✅ | Non |",
            "| Dernier état sain / publication fail-closed | ✅ | Non garanti |",
            "| Projection francophone dédiée | ✅ | Variable |",
            "",
            "La source machine des preuves est [`automation/provider-device-results.json`](automation/provider-device-results.json). Les logos affichés privilégient les assets WebP committés de NiakVIO ; les noms du tableau viennent du même registre de branding mais restent volontairement sans emoji à côté du logo. Les preuves des prochains gros Deep/Labs complètent automatiquement les lignes existantes.",
            END,
        ]
    )
    return "\n".join(lines)


def replace_section(readme: str, section: str) -> str:
    if START in readme and END in readme:
        before, rest = readme.split(START, 1)
        _old, after = rest.split(END, 1)
        return before.rstrip() + "\n\n" + section + after
    anchor = "\n---\n\n# Architecture technique"
    if anchor not in readme:
        raise ValueError("README insertion anchor not found")
    return readme.replace(anchor, "\n---\n\n" + section + "\n\n---\n\n# Architecture technique", 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--diagnostics-root", type=Path)
    parser.add_argument("--run-id", default="manual")
    parser.add_argument("--results", type=Path, default=ROOT / "automation" / "provider-device-results.json")
    parser.add_argument("--readme", type=Path, default=ROOT / "README.md")
    args = parser.parse_args()

    results = load_json(args.results, {"schemaVersion": 1, "fixtures": {}, "proofs": []})
    merge_diagnostics(results, args.diagnostics_root or Path("__missing__"), args.run_id)
    results_text = json.dumps(results, ensure_ascii=False, indent=2) + "\n"
    readme_text = args.readme.read_text(encoding="utf-8")
    next_readme = replace_section(readme_text, render(results))
    args.results.parent.mkdir(parents=True, exist_ok=True)
    args.results.write_text(results_text, encoding="utf-8")
    args.readme.write_text(next_readme, encoding="utf-8")
    print(
        f"provider/device README matrix current: active={len(active_providers())} "
        f"proofs={len(results.get('proofs') or [])} updated={results.get('updatedAt') or 'unknown'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
