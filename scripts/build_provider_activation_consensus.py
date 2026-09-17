#!/usr/bin/env python3
"""Build exact-bundle activation consensus from cheap and native evidence.

Positive evidence is monotonic for the exact published bundle SHA: one verified
positive witness can certify a semantic lane. A negative/inconclusive Node probe
can never disable a provider by itself; unresolved lanes are routed to native
fallback and then Brain/Repair.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LANES = ("movie", "tv", "anime")
STATUS_RE = re.compile(
    r"FIELD_NATIVE_PROVIDER_STATUS\s+client=(?P<client>\S+)\s+provider=(?P<provider>\S+)\s+status=(?P<status>\S+)\s+lanes=(?P<lanes>\S+)"
)

def load(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))

def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")

def sha256_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

def semantic_types(row: dict[str, Any]) -> list[str]:
    values = row.get("canonicalSupportedTypes")
    if not isinstance(values, list) or not values:
        values = row.get("supportedTypes") or []
    out = []
    for raw in values:
        value = cid(raw)
        if value in LANES and value not in out:
            out.append(value)
    return out

def parse_native_logs(paths: list[Path]) -> dict[str, list[dict[str, Any]]]:
    evidence: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in paths:
        if not path.is_file():
            continue
        for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
            marker = raw.find("FIELD_NATIVE_PROVIDER_STATUS ")
            if marker < 0:
                continue
            line = raw[marker:].strip()
            match = STATUS_RE.search(line)
            if not match:
                continue
            lanes = {}
            for token in match.group("lanes").split(","):
                if ":" not in token:
                    continue
                lane, outcome = token.split(":", 1)
                lane = cid(lane)
                if lane in LANES:
                    lanes[lane] = outcome.strip().casefold()
            provider = cid(match.group("provider"))
            evidence[provider].append({
                "source": "native_lab",
                "client": match.group("client").strip().casefold(),
                "status": match.group("status").strip().upper(),
                "lanes": lanes,
                "log": path.name,
            })
    return dict(evidence)

def build(
    manifest: dict[str, Any],
    *,
    node: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
    native: dict[str, list[dict[str, Any]]] | None = None,
    minimum_yield: float = 0.75,
) -> dict[str, Any]:
    node = node if isinstance(node, dict) else {}
    registry = registry if isinstance(registry, dict) else {}
    native = native if isinstance(native, dict) else {}
    node_by_id = {
        cid(row.get("providerId")): row
        for row in node.get("providers") or []
        if isinstance(row, dict) and cid(row.get("providerId"))
    }
    registry_by_id = registry.get("providers") if isinstance(registry.get("providers"), dict) else {}

    providers = []
    active_rows = [
        row for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and cid(row.get("id")) and row.get("enabled") is not False
    ]
    for row in active_rows:
        provider = cid(row.get("id"))
        filename = str(row.get("filename") or "")
        bundle_sha = sha256_file((ROOT / filename).resolve()) if filename else None
        required = semantic_types(row)
        node_row = node_by_id.get(provider) if isinstance(node_by_id.get(provider), dict) else {}
        reg_row = registry_by_id.get(provider) if isinstance(registry_by_id, dict) and isinstance(registry_by_id.get(provider), dict) else {}
        lane_rows = {}
        certified_types = []

        for lane in required:
            positive = []
            negative = []
            node_lane = (node_row.get("lanes") or {}).get(lane) if isinstance(node_row.get("lanes"), dict) else None
            if (
                bundle_sha
                and node_row.get("bundleSha256") == bundle_sha
                and isinstance(node_lane, dict)
                and node_lane.get("state") == "certified"
            ):
                positive.append({
                    "source": "node_exact_bundle",
                    "fixtureSlug": node_lane.get("fixtureSlug"),
                })
            elif isinstance(node_lane, dict):
                negative.append({
                    "source": "node_probe",
                    "state": node_lane.get("state"),
                    "stages": sorted({
                        str(attempt.get("debugStage") or "")
                        for attempt in node_lane.get("attempts") or []
                        if isinstance(attempt, dict) and str(attempt.get("debugStage") or "")
                    }),
                    "authoritativeForDisable": False,
                })

            reg_lane = (reg_row.get("lanes") or {}).get(lane) if isinstance(reg_row.get("lanes"), dict) else None
            if (
                bundle_sha
                and isinstance(reg_lane, dict)
                and reg_lane.get("state") == "certified"
                and reg_lane.get("bundleSha256") == bundle_sha
            ):
                positive.append({
                    "source": "positive_fixture_memory_exact_bundle",
                    "fixtureSlug": reg_lane.get("fixtureSlug"),
                })

            for item in native.get(provider) or []:
                outcome = (item.get("lanes") or {}).get(lane)
                if outcome == "positive":
                    positive.append({
                        "source": "native_lab",
                        "client": item.get("client"),
                        "status": item.get("status"),
                        "log": item.get("log"),
                    })
                elif outcome:
                    negative.append({
                        "source": "native_lab",
                        "client": item.get("client"),
                        "outcome": outcome,
                        "authoritativeForDisable": False,
                    })

            certified = bool(positive)
            if certified:
                certified_types.append(lane)
            lane_rows[lane] = {
                "state": "certified" if certified else "native-fallback-required",
                "positiveEvidence": positive,
                "inconclusiveOrNegativeEvidence": negative,
                "nodeNegativeCanDisable": False,
            }

        missing = [lane for lane in required if lane not in certified_types]
        providers.append({
            "providerId": provider,
            "filename": filename,
            "bundleSha256": bundle_sha,
            "requiredTypes": required,
            "certifiedTypes": certified_types,
            "missingTypes": missing,
            "certified": bool(required) and not missing,
            "activationAction": "keep_or_activate" if required and not missing else "native_fallback_then_brain",
            "disableEligible": False,
            "lanes": lane_rows,
        })

    certified = [row for row in providers if row["certified"]]
    total = len(providers)
    ratio = len(certified) / total if total else 1.0
    minimum_yield = max(0.0, min(float(minimum_yield), 1.0))
    return {
        "schemaVersion": 1,
        "authority": "provider-activation-consensus-v1",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "manifestVersion": manifest.get("version"),
        "activeCandidateCount": total,
        "certifiedCount": len(certified),
        "pendingNativeFallbackCount": total - len(certified),
        "autoCertificationRatio": round(ratio, 4),
        "minimumAutoCertificationRatio": minimum_yield,
        "architectureState": "auto-yield-sufficient" if total < 8 or ratio >= minimum_yield else "architecture-defect-low-auto-yield",
        "negativeNodeEvidenceCanDisable": False,
        "providers": providers,
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "manifest.json")
    parser.add_argument("--node-certification", type=Path)
    parser.add_argument("--positive-registry", type=Path, default=ROOT / "automation/provider-positive-fixtures.json")
    parser.add_argument("--native-log", action="append", type=Path, default=[])
    parser.add_argument("--minimum-yield", type=float, default=0.75)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = load(args.manifest.resolve(), {}) or {}
    node = load(args.node_certification.resolve(), {}) if args.node_certification else {}
    registry = load(args.positive_registry.resolve(), {}) or {}
    native = parse_native_logs([path.resolve() for path in args.native_log])
    payload = build(manifest, node=node, registry=registry, native=native, minimum_yield=args.minimum_yield)
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_PROVIDER_ACTIVATION_CONSENSUS "
        f"certified={payload['certifiedCount']}/{payload['activeCandidateCount']} "
        f"pending_native={payload['pendingNativeFallbackCount']} ratio={payload['autoCertificationRatio']:.4f} "
        f"architecture={payload['architectureState']}"
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
