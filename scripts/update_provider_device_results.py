#!/usr/bin/env python3
"""Merge native-reader evidence and render the README provider showcase.

The visible inventory is derived from enabled scrapers in the general manifest,
so it cannot silently drift from the plugin users actually load. Native-reader
proofs are crossed onto that inventory as they arrive; missing proof stays unknown
rather than being misreported as a provider failure.

The README intentionally showcases retained positive player evidence first. The
complete active inventory remains available in a compact disclosure block without
a wall of empty per-device cells that could be mistaken for failures.
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
DEVICE_ICONS = {
    "tv": "📺",
    "mobile": "📱",
    "desktop_macos": "🖥️",
    "desktop_windows": "🪟",
}
MEDIA_ICONS = {
    "movie": "🎬",
    "tv": "📺",
    "anime": "🎌",
}


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


def media_icon(value: str) -> str:
    return MEDIA_ICONS.get(str(value).casefold(), "🎞️")


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
    native_proof_count = 0
    for row in matching:
        fixture = str(row.get("fixture") or "").strip()
        fixture_row = fixtures.get(fixture) if isinstance(fixtures.get(fixture), dict) else {}
        # The corpus/fixture identity is canonical for display. A provider may expose
        # an anime through a generic TV route; that transport/request shape must not
        # relabel the actual work as a non-anime series in public evidence.
        media_type = str(fixture_row.get("mediaType") or row.get("mediaType") or "unknown").casefold()
        label = str(fixture_row.get("label") or fixture.replace("-", " ").title())
        kind = media_label(media_type)
        content = f"{media_icon(media_type)} {label} · {kind}" if label else f"{media_icon(media_type)} {kind}"
        if content not in seen_content:
            seen_content.add(content)
            verified_content.append(content)
        for device, proof in (row.get("devices") or {}).items():
            if not isinstance(proof, dict):
                continue
            date = str(proof.get("verifiedAt") or "")
            if not date:
                continue
            native_proof_count += 1
            if date >= devices.get(str(device), ""):
                devices[str(device)] = date
    return {
        "proofCount": len(matching),
        "nativeProofCount": native_proof_count,
        "content": verified_content,
        "devices": devices,
        "latest": max(devices.values(), default="—"),
    }


def provider_label(provider: dict[str, Any]) -> str:
    name = html.escape(str(provider.get("name") or provider.get("id") or ""), quote=False).replace("|", "&#124;")
    logo = html.escape(str(provider.get("logo") or ""), quote=True)
    if not logo:
        return f"**{name}**"
    return f'<img src="{logo}" width="42" alt="">&nbsp; **{name}**'


def native_device_cell(summary: dict[str, Any]) -> str:
    devices = summary.get("devices") or {}
    labels = []
    for key, label in DEVICES:
        if str(devices.get(key) or ""):
            labels.append(f"{DEVICE_ICONS.get(key, '✅')} **{label}** ✅")
    return "<br>".join(labels) or ""


def shield(label: str, value: str, color: str) -> str:
    clean_label = str(label).replace("-", "--").replace("_", "__").replace(" ", "_")
    clean_value = str(value).replace("-", "--").replace("_", "__").replace(" ", "_")
    return f"![{label}](https://img.shields.io/badge/{clean_label}-{clean_value}-{color}?style=for-the-badge)"


def render(results: dict[str, Any]) -> str:
    fixtures = fixture_catalog(results)
    providers = active_providers()
    summaries = {provider["key"]: provider_proof_summary(provider, results, fixtures) for provider in providers}
    verified = [provider for provider in providers if summaries[provider["key"]].get("nativeProofCount", 0) > 0]
    verified.sort(
        key=lambda provider: (
            -len(summaries[provider["key"]].get("devices") or {}),
            -int(summaries[provider["key"]].get("nativeProofCount") or 0),
            str(provider.get("name") or "").casefold(),
        )
    )
    positive_dates = [
        str(summary.get("latest"))
        for summary in summaries.values()
        if str(summary.get("latest") or "") not in ("", "—")
    ]
    last_update = str(results.get("updatedAt") or max(positive_dates, default="—"))
    native_proofs = sum(int(summary.get("nativeProofCount") or 0) for summary in summaries.values())
    verified_cases = {
        str(content)
        for summary in summaries.values()
        for content in (summary.get("content") or [])
        if str(content).strip()
    }
    device_coverage = {
        device
        for summary in summaries.values()
        for device, date in (summary.get("devices") or {}).items()
        if str(date or "")
    }
    platform_label = "plateforme native" if len(device_coverage) == 1 else "plateformes natives"

    device_stats: dict[str, dict[str, Any]] = {}
    for device, label in DEVICES:
        proof_count = 0
        provider_count = 0
        dates: list[str] = []
        for provider in providers:
            summary = summaries[provider["key"]]
            date = str((summary.get("devices") or {}).get(device) or "")
            if not date:
                continue
            provider_count += 1
            dates.append(date)
            for row in (results.get("proofs") or []):
                if not isinstance(row, dict):
                    continue
                if str(row.get("provider") or "").strip().casefold() != provider["key"]:
                    continue
                proof = (row.get("devices") or {}).get(device)
                if isinstance(proof, dict) and str(proof.get("verifiedAt") or ""):
                    proof_count += 1
        device_stats[device] = {
            "label": label,
            "proofCount": proof_count,
            "providerCount": provider_count,
            "latest": max(dates, default="—"),
        }

    lines = [
        START,
        "## Providers actifs & résultats natifs vérifiés",
        "",
        '<div align="center">',
        "",
        shield("PROVIDERS ACTIFS", str(len(providers)), "16a34a"),
        shield("NATIFS VERIFIES", str(len(verified)), "2563eb"),
        shield("PREUVES LECTEUR", str(native_proofs), "7c3aed"),
        shield("DERNIERE PREUVE", last_update, "334155"),
        "",
        "</div>",
        "",
        "> **Ici, NiakVIO n'affiche que des succès natifs réellement conservés.** Une preuve signifie que le lecteur officiel Nuvio a atteint un état sain pour le **provider + fixture de test + device exacts**. L'absence de preuve n'est jamais maquillée en succès — et n'est pas non plus présentée comme un échec.",
        "",
        "> **Cadre des œuvres citées :** les titres/épisodes du tableau sont des **fixtures de test**, pas un catalogue ni une offre de contenu. Les résultats décrivent uniquement une observation technique sanitizée. Voir [`TESTING_NOTICE.md`](TESTING_NOTICE.md) et [`DISCLAIMER.md`](DISCLAIMER.md).",
        "",
        f"**{len(verified)} providers** disposent actuellement d'au moins une preuve lecteur native conservée, sur **{len(verified_cases)} cas de lecture distincts** et **{len(device_coverage)} {platform_label}** déjà représentée{'s' if len(device_coverage) != 1 else ''}. L'inventaire complet reste synchronisé automatiquement sur `manifest.json`.",
        "",
        "### 📡 Couverture des lecteurs officiels",
        "",
        "Cette vue distingue **support du lecteur** et **preuve positive conservée** : les quatre familles sont suivies en permanence, même lorsqu'aucune preuve saine n'a encore été retenue pour l'une d'elles.",
        "",
        "| Lecteur officiel | Preuves positives conservées | Providers avec preuve | Dernière preuve | État |",
        "|---|---:|---:|---:|---|",
    ]

    for device, label in DEVICES:
        stat = device_stats[device]
        proof_count = int(stat.get("proofCount") or 0)
        provider_count = int(stat.get("providerCount") or 0)
        latest = str(stat.get("latest") or "—")
        state = "✅ Couvert par une preuve native" if proof_count else "🟡 Suivi actif · aucune preuve positive conservée"
        lines.append(
            f"| {DEVICE_ICONS.get(device, '🧩')} **{label}** | **{proof_count}** | **{provider_count}** | `{latest}` | {state} |"
        )

    lines.extend(
        [
            "",
            "### ✅ Lectures natives confirmées",
            "",
            "| Provider | Fixtures de test réellement validées | Lecteurs officiels confirmés | Preuves | Dernière validation |",
        "|---|---|---|---:|---:|",
        ]
    )

    for provider in verified:
        summary = summaries[provider["key"]]
        contents = "<br>".join(str(value).replace("|", "\\|") for value in summary.get("content") or [])
        lines.append(
            "| {provider} | {contents} | {devices} | **{proofs}** | `{date}` |".format(
                provider=provider_label(provider),
                contents=contents,
                devices=native_device_cell(summary),
                proofs=summary.get("nativeProofCount") or 0,
                date=summary.get("latest") or "—",
            )
        )

    if not verified:
        lines.append("| _Aucune preuve positive conservée pour le moment_ | — | — | 0 | — |")

    lines.extend(
        [
            "",
            "<details>",
            f"<summary><strong>🟢 Voir les {len(providers)} providers actifs</strong> — inventaire complet synchronisé au manifest</summary>",
            "",
            "La liste ci-dessous décrit **l'état de publication**, pas une supposition sur la lecture. Les providers déjà prouvés natifs sont signalés ; les autres restent simplement actifs dans le manifest jusqu'à ce qu'une preuve positive soit conservée.",
            "",
            "| Provider | Types publiés | État de confiance public |",
            "|---|---|---|",
        ]
    )

    inventory = sorted(
        providers,
        key=lambda provider: (
            0 if summaries[provider["key"]].get("nativeProofCount", 0) > 0 else 1,
            str(provider.get("name") or "").casefold(),
        ),
    )
    for provider in inventory:
        summary = summaries[provider["key"]]
        types = " · ".join(
            f"{media_icon(value)} {media_label(value)}" for value in provider.get("types") or []
        ) or "Type non déclaré"
        proof_count = int(summary.get("nativeProofCount") or 0)
        if proof_count:
            proof_label = "validation lecteur" if proof_count == 1 else "validations lecteur"
            state = f"✅ **Preuve native conservée** · {proof_count} {proof_label}"
        else:
            state = "🟢 **Actif dans le manifest** · prochaine preuve native conservée dès validation positive"
        lines.append(f"| {provider_label(provider)} | {types} | {state} |")

    lines.extend(
        [
            "",
            "</details>",
            "",
            "### Pourquoi ces résultats sont plus stricts qu'une simple liste de providers",
            "",
            "| Contrôle | NiakVIO | Manifest/provider brut |",
            "|---|---|---|",
            "| Provider présent dans un manifest | ✅ | ✅ |",
            "| Plusieurs upstreams comparés avant promotion | ✅ | Variable |",
            "| Média final réellement atteint | ✅ | Non garanti |",
            "| Lecteur officiel vérifié par plateforme | ✅ TV / Mobile / macOS / Windows | Non garanti |",
            "| Identité œuvre / année / saison / épisode contrôlée | ✅ | Non garanti |",
            "| HLS / DASH / média direct validé au-delà de l'extension URL | ✅ | Non garanti |",
            "| Mauvais média jouable classé comme échec | ✅ | Non garanti |",
            "| Repair Brain puis retest avant promotion | ✅ | Non |",
            "| Dernier état sain + publication fail-closed | ✅ | Non garanti |",
            "| Historique machine des preuves positives | ✅ | Variable |",
            "",
            "**Lecture de la vitrine :** `✅` signifie *preuve positive conservée*, jamais simple détection d'URL. Les résultats affichés restent fixes tant qu'une nouvelle preuve native plus récente ne vient pas les compléter ; un run inconclusif ne détruit pas une preuve saine existante.",
            "",
            "Source machine : [`automation/provider-device-results.json`](automation/provider-device-results.json) · Inventaire : [`manifest.json`](manifest.json) · Les prochains Deep/Brain/Labs enrichissent automatiquement cette vitrine uniquement avec des preuves positives qualifiées.",
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
        f"provider/device README showcase current: active={len(active_providers())} "
        f"proofs={len(results.get('proofs') or [])} updated={results.get('updatedAt') or 'unknown'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
