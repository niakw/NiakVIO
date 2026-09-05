#!/usr/bin/env python3
"""Extract repair-relevant provenance without promoting it to executable route DATA.

PROVENANCE.json contains historical/deep evidence, activation gates, observed provider
hosts and source metadata.  It is valuable for classifying failures (type/gate vs
network/policy/domain), but it is not an authoritative route-plan source.  This helper
emits a compact per-provider diagnostic index consumed by repair workflows and tests.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROVENANCE = ROOT / "PROVENANCE.json"
OUTPUT = ROOT / "automation" / "provider-v3-repair-provenance-index.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: object required")
    return value


def unique(values: list[Any], limit: int = 64) -> list[str]:
    out: list[str] = []
    for raw in values:
        value = str(raw or "").strip()
        if value and value not in out:
            out.append(value)
        if len(out) >= limit:
            break
    return out


def provider_server_evidence(row: dict[str, Any]) -> dict[str, Any]:
    gates = row.get("activation_gates") if isinstance(row.get("activation_gates"), dict) else {}
    access = gates.get("00_provider_specific_access") if isinstance(gates.get("00_provider_specific_access"), dict) else {}
    evidence = access.get("evidence") if isinstance(access.get("evidence"), dict) else {}
    dns_gate = gates.get("00_dns_or_alternative_domain") if isinstance(gates.get("00_dns_or_alternative_domain"), dict) else {}
    dns_evidence = dns_gate.get("evidence") if isinstance(dns_gate.get("evidence"), dict) else {}
    return {
        "providerServerSuccessfulResponse": bool(evidence.get("provider_server_successful_response")),
        "providerServerHosts": unique(list(evidence.get("provider_server_hosts") or [])),
        "providerServerHttpStatuses": sorted({int(v) for v in evidence.get("provider_server_http_statuses") or [] if str(v).isdigit()}),
        "dnsStatus": str(dns_evidence.get("dns_status") or "").strip() or None,
    }


def summarize(provenance: dict[str, Any]) -> dict[str, Any]:
    providers = provenance.get("providers") if isinstance(provenance.get("providers"), dict) else {}
    out: dict[str, Any] = {
        "schemaVersion": 1,
        "role": "diagnostic-only-not-route-authority",
        "sourceSchemaVersion": provenance.get("schema_version"),
        "sourceGeneratedAt": provenance.get("generated_at"),
        "providers": {},
    }
    for provider_id, raw in providers.items():
        if not isinstance(raw, dict):
            continue
        access = provider_server_evidence(raw)
        blockers = unique(list(raw.get("activation_blockers") or []), 32)
        statuses = access["providerServerHttpStatuses"]
        out["providers"][str(provider_id).casefold()] = {
            "routeAuthority": False,
            "source": raw.get("source"),
            "sourceName": raw.get("source_name"),
            "checkedAt": raw.get("checked_at"),
            "checkMode": raw.get("check_mode"),
            "checkStatus": raw.get("check_status"),
            "healthScore": raw.get("health_score"),
            "activationEligible": bool(raw.get("activation_eligible")),
            "activationBlockers": blockers,
            **access,
            "failureFamilyHints": {
                "hasSuccessfulProviderHttp": bool(access["providerServerSuccessfulResponse"]),
                "blockedOrPolicyHttpOnly": bool(statuses) and set(statuses).issubset({401, 403, 407, 429, 451}),
                "mixed403404Or522": bool(set(statuses) & {403, 404, 522}) and len(set(statuses) & {403, 404, 522}) >= 2,
                "routeMustNotBeInventedFromProvenance": True,
            },
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provenance", type=Path, default=PROVENANCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    provenance = load(args.provenance.resolve())
    summary = summarize(provenance)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_PROVIDER_PROVENANCE_REPAIR_INDEX "
        f"providers={len(summary['providers'])} route_authority=false "
        f"source_schema={summary.get('sourceSchemaVersion')}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
