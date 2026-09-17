#!/usr/bin/env python3
"""Build a cluster-first Brain queue from exact-bundle certification failures.

The Brain must not treat a low-yield onboarding run as hundreds of unrelated
provider failures. It groups unresolved lanes by reusable failure signature so a
single Core/capability repair can recover an entire family before provider-local
learning is attempted.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

CLASS_BY_STAGE = {
    "provider_network_zero_result": "route_or_catalog_resolution",
    "provider_network_http_error": "request_transport_or_upstream",
    "provider_network_exception": "runtime_compatibility",
    "provider_returned_streams": "playback_or_identity_verification",
    "timeout": "timeout_or_rate_limit",
    "invalid_probe_output": "probe_infrastructure",
    "provider_zero_before_network": "runtime_plan_execution",
    "provider_zero_before_provider_network": "identity_or_route_gate",
    "gate_source_family_unknown": "source_family_detection",
    "gate_runtime_plan_missing": "runtime_plan_detection",
    "gate_type_capability": "capability_mapping",
}

def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path}: object required")
    return value

def classify(stages: list[str]) -> str:
    classes = [CLASS_BY_STAGE.get(stage, "unknown_failure") for stage in stages if stage]
    if not classes:
        return "unknown_failure"
    counts = Counter(classes)
    return sorted(counts, key=lambda item: (-counts[item], item))[0]

def build(certification: dict[str, Any]) -> dict[str, Any]:
    clusters: dict[tuple[str, str, tuple[str, ...]], list[str]] = defaultdict(list)
    providers: list[dict[str, Any]] = []
    for row in certification.get("providers") or []:
        if not isinstance(row, dict) or row.get("enabled") is not True or row.get("certified") is True:
            continue
        pid = str(row.get("providerId") or "").strip()
        lane_rows = []
        for lane, data in sorted((row.get("lanes") or {}).items()):
            if not isinstance(data, dict) or data.get("state") == "certified":
                continue
            stages = sorted({
                str(a.get("debugStage") or "").strip()
                for a in data.get("attempts") or []
                if isinstance(a, dict) and str(a.get("debugStage") or "").strip()
            })
            failure_class = classify(stages)
            signature = (failure_class, str(lane), tuple(stages))
            clusters[signature].append(pid)
            lane_rows.append({
                "lane": lane,
                "failureClass": failure_class,
                "stages": stages,
                "attemptCount": int(data.get("attemptCount") or 0),
            })
        providers.append({
            "providerId": pid,
            "missingTypes": list(row.get("missingTypes") or []),
            "lanes": lane_rows,
        })

    cluster_rows = []
    for (failure_class, lane, stages), ids in clusters.items():
        cluster_rows.append({
            "failureClass": failure_class,
            "lane": lane,
            "stages": list(stages),
            "providerCount": len(set(ids)),
            "providers": sorted(set(ids)),
            "repairScope": "core_or_capability_family_first",
        })
    cluster_rows.sort(key=lambda row: (-row["providerCount"], row["failureClass"], row["lane"], row["providers"]))
    active = int(certification.get("activeProviderCount") or 0)
    certified = int(certification.get("certifiedActiveProviderCount") or 0)
    ratio = certified / active if active else 1.0
    return {
        "schemaVersion": 1,
        "authority": "provider-certification-cluster-learning-v1",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sourceAuthority": certification.get("authority"),
        "manifestVersion": certification.get("manifestVersion"),
        "activeProviderCount": active,
        "certifiedActiveProviderCount": certified,
        "autoCertificationRatio": round(ratio, 4),
        "architectureState": "auto-yield-sufficient" if active < 8 or ratio >= 0.75 else "architecture-defect-low-auto-yield",
        "strategy": "largest_shared_failure_cluster_first",
        "clusters": cluster_rows,
        "providers": providers,
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--certification", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = build(load(args.certification.resolve()))
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_PROVIDER_CERTIFICATION_LEARNING "
        f"certified={payload['certifiedActiveProviderCount']}/{payload['activeProviderCount']} "
        f"ratio={payload['autoCertificationRatio']:.4f} architecture={payload['architectureState']} "
        f"clusters={len(payload['clusters'])}"
    )
    for row in payload["clusters"][:12]:
        print(
            "FIELD_PROVIDER_FAILURE_CLUSTER "
            f"class={row['failureClass']} lane={row['lane']} providers={row['providerCount']} "
            f"stages={','.join(row['stages']) or 'none'}"
        )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
