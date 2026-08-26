#!/usr/bin/env python3
"""Validate and render the audited Nuvio cross-client runtime contract matrix."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "platform-runtime-contracts.json"
README = ROOT / "automation" / "PLATFORM-RUNTIME-CONTRACTS.md"

LABELS = {
    "runtime_engine": "Runtime JS",
    "get_streams_signature": "Signature getStreams",
    "scraper_id": "SCRAPER_ID",
    "scraper_settings": "SCRAPER_SETTINGS",
    "tmdb_api_key": "TMDB_API_KEY",
    "fetch_bridge": "fetch / bridge natif",
    "http_stack": "Pile HTTP",
    "proxy_policy": "Politique proxy",
    "dns_policy": "DNS",
    "redirects": "Redirections",
    "timeouts": "Timeouts",
    "abort_controller": "AbortController",
    "url_api": "URL / URLSearchParams",
    "base64": "atob / btoa",
    "text_codec": "TextEncoder / TextDecoder",
    "cheerio_dom": "Cheerio / DOM",
    "require_commonjs": "require / CommonJS",
    "cryptojs": "CryptoJS / crypto",
    "webassembly": "WebAssembly",
    "exception_to_empty": "Exception getStreams → []",
    "stream_headers": "Headers stream",
    "subtitles": "Sous-titres stream",
    "torrent_fields": "seeders / peers / infoHash",
    "behavior_hints_projection": "Projection behaviorHints / proxyHeaders",
}


def load_contract() -> dict:
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if data.get("schema_version") != 2:
        raise SystemExit("platform runtime contract schema_version must be 2")
    clients = data.get("clients")
    if not isinstance(clients, dict) or not clients:
        raise SystemExit("platform runtime contract requires clients")
    states = set(data.get("capability_state_vocabulary") or [])
    order = data.get("capability_order") or []
    if not states or not order:
        raise SystemExit("platform runtime contract requires capability state vocabulary and order")
    if len(order) != len(set(order)):
        raise SystemExit("platform runtime contract capability_order contains duplicates")
    missing_labels = [key for key in order if key not in LABELS]
    if missing_labels:
        raise SystemExit(f"missing renderer labels: {','.join(missing_labels)}")

    for client_id, client in clients.items():
        for key in ("display_name", "family", "source_repository", "source_branch", "source_ref", "audit_status", "audited_at"):
            if not client.get(key):
                raise SystemExit(f"{client_id}: missing {key}")
        ref = str(client["source_ref"])
        if len(ref) != 40 or any(ch not in "0123456789abcdef" for ch in ref.lower()):
            raise SystemExit(f"{client_id}: source_ref is not a full Git SHA")
        capabilities = client.get("capabilities") or {}
        missing = [key for key in order if key not in capabilities]
        extra = sorted(set(capabilities) - set(order))
        if missing or extra:
            raise SystemExit(f"{client_id}: capability mismatch missing={missing} extra={extra}")
        for key in order:
            value = capabilities[key]
            if not isinstance(value, dict):
                raise SystemExit(f"{client_id}:{key}: capability must be an object")
            state = value.get("state")
            detail = value.get("detail")
            if state not in states:
                raise SystemExit(f"{client_id}:{key}: invalid state {state!r}")
            if not isinstance(detail, str) or not detail.strip():
                raise SystemExit(f"{client_id}:{key}: missing detail")
    return data


def esc(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def cell(capability: dict) -> str:
    return f"**{esc(capability['state'])}** — {esc(capability['detail'])}"


def render(data: dict) -> str:
    clients = data["clients"]
    ids = list(clients)
    order = data["capability_order"]
    lines = [
        "# Contrat runtime Nuvio — comparaison par device",
        "",
        "> Généré depuis `automation/platform-runtime-contracts.json` par `scripts/render_platform_runtime_contracts.py`. Ne pas éditer la matrice à la main.",
        "",
        f"Dernier audit du contrat : **{esc(data['audited_at'])}**.",
        "",
        "## Matrice des capacités",
        "",
        "| Capacité | " + " | ".join(esc(clients[cid]["display_name"]) for cid in ids) + " |",
        "| --- | " + " | ".join("---" for _ in ids) + " |",
    ]
    for key in order:
        lines.append("| " + esc(LABELS[key]) + " | " + " | ".join(cell(clients[cid]["capabilities"][key]) for cid in ids) + " |")

    lines += [
        "",
        "## Révisions auditées",
        "",
        "| Device | Dépôt / branche | Révision auditée | État | Transport runtime |",
        "| --- | --- | --- | --- | --- |",
    ]
    for cid in ids:
        client = clients[cid]
        lines.append(
            f"| {esc(client['display_name'])} | `{esc(client['source_repository'])}` / `{esc(client['source_branch'])}` | "
            f"`{esc(client['source_ref'])}` | **{esc(client['audit_status'])}** | `{esc(client['transport_source'])}` |"
        )

    lines += [
        "",
        "## Lecture des états",
        "",
        "- **native** : comportement fourni directement par le client ou son modèle natif.",
        "- **bridge** : capacité exposée à JavaScript par un pont natif.",
        "- **polyfill** : compatibilité fournie en JavaScript au-dessus du runtime.",
        "- **shim** : adaptation NiakVIO explicitement nécessaire pour harmoniser les clients.",
        "- **absent** : capacité absente du contrat actuel du client.",
        "- **incompatible** : capacité présente mais avec une sémantique incompatible entre clients.",
        "- **audit-required** : le code upstream a changé et la valeur ne doit pas être considérée comme validée avant ré-audit.",
        "- **n/a** : capacité sans objet pour ce client.",
        "",
        "## Différences qui comptent pour NiakVIO",
        "",
        "- **Android et Android TV forcent `Proxy.NO_PROXY`; Desktop ne le force pas.** C'est une différence de transport silencieuse : un provider peut attraper une erreur réseau et retourner `[]` sans exception JavaScript visible.",
        "- **Desktop utilise un bridge `__native_fetch` asynchrone**, alors que Mobile et TV appellent leur pont natif de manière bloquante derrière l'API JavaScript `fetch`.",
        "- **iOS utilise Ktor/Darwin**, contrairement à l'OkHttp d'Android, Desktop et TV. Les comportements réseau propres à la plateforme doivent donc rester audités séparément.",
        "- **TV injecte `TMDB_API_KEY` dans le runtime plugin; Mobile/Desktop ne l'exposent pas comme global runtime.** Un provider portable ne doit pas dépendre de ce global sans fallback.",
        "- **Mobile/Desktop conservent `subtitles`; TV ne possède pas ce champ dans `LocalScraperResult`.** Les sous-titres retournés uniquement par un provider JS ne sont donc pas projetables de manière identique sur TV aujourd'hui.",
        "- **TV projette les headers dans `behaviorHints.proxyHeaders.request`** et ajoute son `bingeGroup`; Mobile/Desktop conservent d'abord les headers bruts dans `PluginRuntimeResult`.",
        "- **TV n'expose actuellement ni TextEncoder/TextDecoder ni WebAssembly dans son PluginRuntime**, contrairement au runtime Mobile/Desktop. Un provider qui en dépend doit être adapté ou déclaré incompatible TV.",
        "",
        "## Contrat vivant / drift upstream",
        "",
        f"Le registre `{esc(data['drift_contract']['registry'])}` et le checker `{esc(data['drift_contract']['checker'])}` surveillent les HEAD officiels Mobile, Desktop et TV. "
        "Les chemins runtime, modèles de résultat, repository et transport font partie du périmètre sensible.",
        "",
        "Règle : **un HEAD ne doit pas être avancé comme contrat audité lorsqu'un de ces chemins ou une sémantique sensible a changé sans ré-audit**. Après audit, `source_ref`, le registre upstream et cette matrice doivent pointer vers la même révision officielle.",
        "",
        "Le check CI `python3 scripts/render_platform_runtime_contracts.py --check` garantit que ce README reste exactement synchronisé avec le JSON machine-readable.",
        "",
        "## Sources canoniques par client",
        "",
    ]
    for cid in ids:
        client = clients[cid]
        lines += [
            f"### {esc(client['display_name'])}",
            "",
            f"- Runtime : `{esc(client['runtime_source'])}`",
            f"- Repository : `{esc(client['repository_source'])}`",
            f"- Transport : `{esc(client['transport_source'])}`",
            f"- Modèle de résultat : `{esc(client['result_model_source'])}`",
            f"- Note d'audit : {esc(client['audit_note'])}",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = load_contract()
    expected = render(data)
    if args.check:
        actual = README.read_text(encoding="utf-8") if README.exists() else ""
        if actual != expected:
            raise SystemExit("PLATFORM-RUNTIME-CONTRACTS.md is stale; run the renderer")
        print("platform runtime contract README is current")
        return 0
    README.write_text(expected, encoding="utf-8")
    print(f"rendered {README.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
