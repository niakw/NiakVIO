#!/usr/bin/env python3
"""Classify native-reader failures by the layer that owns the next action.

The classifier is deliberately conservative:
- Lab/emulator/runner failures are infrastructure defects owned by NiakVIO Labs and
  may block final validation because the evidence itself is unreliable.
- Official Nuvio client/runtime failures are vendor-wait observations. They remain
  visible but do not block provider publication and never authorize provider JS edits.
- Provider/media/transport failures are Brain/Deep learning targets. A failed repair
  is still a valid learning result and never blocks a healthy manifest transaction.
- Repository/manifest loading issues stay a separate Core/manifest-review bucket;
  they are not automatically blamed on either the provider JS or the Nuvio vendor.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

LAB_PATTERNS = (
    re.compile(r"\badb\b", re.I),
    re.compile(r"device[_ ]?offline", re.I),
    re.compile(r"\bemulator\b", re.I),
    re.compile(r"\bqemu\b", re.I),
    re.compile(r"\bavd\b", re.I),
    re.compile(r"\bkvm\b", re.I),
    re.compile(r"runner.*(?:shutdown|cancel|terminated|killed)", re.I),
    re.compile(r"boot.*(?:timeout|failed)", re.I),
    re.compile(r"no[_ ]readable[_ ]logs", re.I),
    re.compile(r"(?:missing|no)[_ ]route[_ ]log", re.I),
)

CLIENT_RUNTIME_CLASSES = {
    "playback_runtime_setup",
    "playback_player_error",
    "playback_decoder",
}


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def clean(value: Any, limit: int = 180) -> str:
    text = str(value or "").strip()
    folded = text.casefold()
    if "://" in text or any(token in folded for token in ("authorization=", "cookie=", "token=", "secret=")):
        return ""
    return re.sub(r"\s+", " ", text)[:limit]


def is_lab_problem(value: Any) -> bool:
    text = clean(value, 500)
    return bool(text and any(pattern.search(text) for pattern in LAB_PATTERNS))


def classify_observation(row: dict[str, Any]) -> str | None:
    if str(row.get("routeMode") or row.get("route_mode") or "").casefold() == "capability_probe":
        return None
    failure = clean(row.get("failureClass") or row.get("failure_class"), 96) or "unknown_failure"
    if failure == "healthy":
        return None
    domain = clean(row.get("failureDomain") or row.get("failure_domain"), 64).casefold()
    details = " ".join(
        clean(row.get(key), 240)
        for key in ("errorClass", "errorCode", "exceptionChain", "reason")
        if row.get(key)
    )
    if domain == "lab_emulation" or is_lab_problem(details):
        return "lab_emulation"
    if domain == "client_runtime" or failure in CLIENT_RUNTIME_CLASSES:
        return "nuvio_vendor_wait"
    if domain in {"provider_stream", "provider_extraction"} or bool(row.get("providerMutationEligible")):
        return "provider_learning"
    if str(row.get("failureStage") or "").casefold() == "media_extraction":
        return "provider_learning"
    return "unresolved_nonblocking"


def classify_report(path: Path, report: dict[str, Any]) -> tuple[Counter[str], list[dict[str, str]]]:
    counts: Counter[str] = Counter()
    samples: list[dict[str, str]] = []

    for problem in report.get("evidenceProblems") or []:
        if is_lab_problem(problem):
            counts["lab_emulation"] += 1
            if len(samples) < 80:
                samples.append({"file": path.name, "owner": "lab_emulation", "reason": clean(problem)})

    observations = [row for row in report.get("observations") or [] if isinstance(row, dict)]
    for row in observations:
        owner = classify_observation(row)
        if owner is None:
            continue
        counts[owner] += 1
        if len(samples) < 80:
            samples.append(
                {
                    "file": path.name,
                    "owner": owner,
                    "provider": clean(row.get("provider"), 96).casefold(),
                    "fixture": clean(row.get("fixture"), 96),
                    "failureClass": clean(row.get("failureClass"), 96) or "unknown_failure",
                }
            )

    for issue in report.get("providerLoadIssues") or []:
        if not isinstance(issue, dict):
            continue
        counts["repository_or_manifest_review"] += 1
        if len(samples) < 80:
            samples.append(
                {
                    "file": path.name,
                    "owner": "repository_or_manifest_review",
                    "provider": clean(issue.get("provider"), 96).casefold(),
                    "fixture": clean(issue.get("fixture"), 96),
                    "failureClass": clean(issue.get("failureClass"), 96) or "provider_repository_load_error",
                }
            )

    # An incomplete report with no emulator/runner signature is still useful to
    # Brain instrumentation learning. It is not sufficient to mutate a provider.
    if report.get("evidenceComplete") is not True and not any(
        row.get("owner") == "lab_emulation" for row in samples
    ):
        counts["incomplete_learning_only"] += 1

    return counts, samples


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--diagnostics-root", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fail-on-lab-infra", action="store_true")
    args = parser.parse_args()

    paths: list[Path] = []
    for root in args.diagnostics_root:
        if root.is_file() and root.name.endswith("brain.json"):
            paths.append(root)
        elif root.exists():
            paths.extend(sorted(root.rglob("*brain.json")))
    paths = sorted(dict.fromkeys(path.resolve() for path in paths))

    total: Counter[str] = Counter()
    samples: list[dict[str, str]] = []
    readable = 0
    for path in paths:
        report = load(path)
        if not report:
            continue
        readable += 1
        counts, rows = classify_report(path, report)
        total.update(counts)
        samples.extend(rows)

    payload = {
        "schemaVersion": 1,
        "diagnosticFiles": readable,
        "ownershipCounts": dict(sorted(total.items())),
        "labEmulationFailures": total["lab_emulation"],
        "nuvioVendorWaitFailures": total["nuvio_vendor_wait"],
        "providerLearningFailures": total["provider_learning"],
        "repositoryOrManifestReview": total["repository_or_manifest_review"],
        "incompleteLearningOnly": total["incomplete_learning_only"],
        "samples": samples[:80],
        "policy": {
            "labEmulationBlocksFinalValidation": True,
            "nuvioVendorWaitBlocksProviderPublication": False,
            "providerLearningBlocksProviderPublication": False,
            "failedRepairBlocksPublication": False,
            "providerMutationRequiresIndependentValidatedEvidence": True,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_NATIVE_READER_OWNERSHIP "
        f"files={readable} lab_emulation={payload['labEmulationFailures']} "
        f"nuvio_vendor_wait={payload['nuvioVendorWaitFailures']} "
        f"provider_learning={payload['providerLearningFailures']} "
        f"repository_review={payload['repositoryOrManifestReview']} "
        f"incomplete_learning_only={payload['incompleteLearningOnly']}"
    )
    if args.fail_on_lab_infra and payload["labEmulationFailures"]:
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
