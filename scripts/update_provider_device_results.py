#!/usr/bin/env python3
"""Merge positive native-reader evidence and render the README result matrix.

Only healthy player observations from complete official native-reader diagnosis
artifacts are accepted. Existing positive proofs are retained as dated evidence;
missing cells are never converted into failures by this script.
"""
from __future__ import annotations

import argparse
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
    return {"movie": "Film", "tv": "Série", "anime": "Anime"}.get(str(value), str(value).title())


def latest_date(row: dict[str, Any]) -> str:
    return max(
        (
            str(proof.get("verifiedAt") or "")
            for proof in (row.get("devices") or {}).values()
            if isinstance(proof, dict)
        ),
        default="—",
    )


def device_cell(row: dict[str, Any], device: str) -> str:
    proof = (row.get("devices") or {}).get(device)
    if not isinstance(proof, dict):
        return "—"
    date = str(proof.get("verifiedAt") or "")
    return f"✅ {date}" if date else "✅"


def render(results: dict[str, Any]) -> str:
    fixtures = fixture_catalog(results)
    rows = [row for row in (results.get("proofs") or []) if isinstance(row, dict)]
    last_update = str(results.get("updatedAt") or max((latest_date(row) for row in rows), default="—"))
    lines = [
        START,
        "## Résultats natifs vérifiés",
        "",
        f"**Dernière mise à jour des preuves positives : {last_update}.**",
        "",
        "Cette matrice ne compte qu'une preuve où le **lecteur officiel Nuvio** a atteint un état sain pour le provider, le contenu et le device indiqués. `—` signifie simplement qu'aucune preuve positive n'est encore conservée pour cette case. Les services tiers pouvant changer, la date reste volontairement visible.",
        "",
        "| Provider | Contenu testé | Type | TV | Mobile | Desktop macOS | Desktop Windows | Dernière preuve |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in sorted(rows, key=lambda value: (str(value.get("fixture")), str(value.get("provider")))):
        fixture = str(row.get("fixture") or "")
        fixture_row = fixtures.get(fixture) if isinstance(fixtures.get(fixture), dict) else {}
        label = str(fixture_row.get("label") or fixture.replace("-", " ").title())
        lines.append(
            "| {provider} | {label} | {kind} | {tv} | {mobile} | {mac} | {win} | {date} |".format(
                provider=str(row.get("provider") or ""),
                label=label.replace("|", "\\|"),
                kind=media_label(str(row.get("mediaType") or fixture_row.get("mediaType") or "unknown")),
                tv=device_cell(row, "tv"),
                mobile=device_cell(row, "mobile"),
                mac=device_cell(row, "desktop_macos"),
                win=device_cell(row, "desktop_windows"),
                date=latest_date(row),
            )
        )
    lines.extend(
        [
            "",
            "### Ce que NiakVIO ajoute à une simple liste de providers",
            "",
            "| Capacité | NiakVIO | Manifest/provider brut |",
            "|---|---|---|",
            "| Plusieurs upstreams comparés | ✅ | Généralement une seule source |",
            "| Preuve lecteur officielle par device | ✅ TV / Mobile / Desktop | Non garantie |",
            "| Vérification œuvre / saison / épisode | ✅ | Non garantie |",
            "| Validation média et premier segment | ✅ | Non garantie |",
            "| Repair Brain + retest après mutation | ✅ | Non |",
            "| Dernier état sain / publication fail-closed | ✅ | Non garanti |",
            "| Projection francophone dédiée | ✅ | Variable |",
            "",
            "La source machine de cette matrice est [`automation/provider-device-results.json`](automation/provider-device-results.json). Les nouveaux diagnostics natifs positifs sont fusionnés sans transformer une absence de preuve en échec.",
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
        f"provider/device README matrix current: proofs={len(results.get('proofs') or [])} "
        f"updated={results.get('updatedAt') or 'unknown'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
