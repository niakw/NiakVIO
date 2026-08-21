#!/usr/bin/env python3
"""Materialize bounded provider-agnostic repair candidates from native-reader Brain evidence.

Native readers are compatibility observers, not authorities that may condemn a
provider globally. A provider mutation is eligible only after the same declared
route and same failure class are corroborated by at least two distinct Nuvio client
families, with no healthy peer at the causal layer. Single-client/OS failures remain
compatibility evidence for future Nuvio updates and Core analysis; they are never
turned into provider JS mutations here.

This remains a Learning Lab mutation step, never publication. Candidate bundles still
require fresh native proof before they can be considered successful.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_PATH = ROOT / "scripts/provider_patches/global_media_enrichment_v1.py"
MIN_DISTINCT_CLIENTS_FOR_GLOBAL_PROVIDER_REPAIR = 2

HYPOTHESIS_SKILLS: dict[str, tuple[str, ...]] = {
    "capture-media-network": ("global_media_enrichment_v1",),
    "inspect-player-javascript": ("global_media_enrichment_v1",),
    "replay-native-request-context": ("global_media_enrichment_v1",),
    "refresh-access-bound-media": ("global_media_enrichment_v1",),
    "refresh-terminal-media-candidate": ("global_media_enrichment_v1",),
    "inspect-unexpected-media-response": ("global_media_enrichment_v1",),
    "resolve-real-media-not-wrapper": ("global_media_enrichment_v1",),
    "repair-reader-io-contract": ("global_media_enrichment_v1",),
    "reject-short-or-preview-media": ("global_media_enrichment_v1",),
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def load_optional(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    try:
        return load_json(path)
    except (OSError, json.JSONDecodeError, ValueError):
        return {}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def safe_fragment(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip(".-")[:100] or "provider"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_patch_module():
    spec = importlib.util.spec_from_file_location("native_reader_global_media_enrichment", PATCH_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {PATCH_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def local_provider_path(filename: str) -> Path:
    raw = str(filename or "").strip()
    if not raw or raw.startswith(("http://", "https://")):
        raise ValueError(f"native reader repair requires an in-repository provider bundle: {raw!r}")
    path = (ROOT / raw).resolve()
    path.relative_to(ROOT.resolve())
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def _key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("provider") or "").casefold().strip(),
        str(row.get("requestType") or row.get("request_type") or "unknown").casefold().strip(),
        str(row.get("fixture") or "").strip(),
    )


def _failure_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    route = _key(row)
    return (*route, str(row.get("failureClass") or "unknown_failure").casefold().strip())


def diagnosis_targets(
    diagnosis: dict[str, Any],
    max_providers: int,
    fixture: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return globally repairable targets plus compatibility-only skips.

    A native failure is globally mutable only when:
      * evidence contains the same provider/request/fixture/failure-class on >=2
        distinct Nuvio client families; and
      * no client has a healthy observation for the same causal layer.

    Player failures are vetoed by a healthy production-player observation. A
    media_extraction_gap is vetoed by any enabled peer that returned at least one
    stream for the same provider/request/fixture, even if that stream later fails
    in the player. This prevents fixing extraction when extraction demonstrably works.

    Windows/macOS remain the same `desktop` family unless the evidence schema later
    exposes distinct production player families. OS-specific failures therefore
    cannot accidentally satisfy cross-client consensus.
    """
    wanted_fixture = str(fixture or "").strip()
    player_healthy_clients: dict[tuple[str, str, str], set[str]] = {}
    extraction_healthy_clients: dict[tuple[str, str, str], set[str]] = {}

    for raw in diagnosis.get("observations") or []:
        if not isinstance(raw, dict):
            continue
        if str(raw.get("routeMode") or raw.get("route_mode") or "declared").casefold() == "capability_probe":
            continue
        if str(raw.get("failureClass") or "").casefold() != "healthy":
            continue
        key = _key(raw)
        if wanted_fixture and key[2] != wanted_fixture:
            continue
        client = str(raw.get("client") or "unknown").casefold().strip() or "unknown"
        player_healthy_clients.setdefault(key, set()).add(client)

    for raw in diagnosis.get("extractionHealthyObservations") or []:
        if not isinstance(raw, dict):
            continue
        if str(raw.get("routeMode") or raw.get("route_mode") or "declared").casefold() == "capability_probe":
            continue
        key = _key(raw)
        if wanted_fixture and key[2] != wanted_fixture:
            continue
        if int(raw.get("returnedCount") or 0) <= 0:
            continue
        client = str(raw.get("client") or "unknown").casefold().strip() or "unknown"
        extraction_healthy_clients.setdefault(key, set()).add(client)

    grouped: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for raw in diagnosis.get("plans") or []:
        if not isinstance(raw, dict):
            continue
        if wanted_fixture and str(raw.get("fixture") or "") != wanted_fixture:
            continue
        if str(raw.get("routeMode") or "declared").casefold() == "capability_probe":
            continue
        provider = str(raw.get("provider") or "").casefold().strip()
        if not provider or str(raw.get("action") or "") != "probe-targeted-repair":
            continue
        key = _failure_key(raw)
        route_key = key[:3]
        failure_class = key[3]
        target = grouped.setdefault(key, {
            "provider": provider,
            "requestType": route_key[1],
            "fixture": route_key[2],
            "failureClasses": [failure_class],
            "hypotheses": [],
            "occurrences": 0,
            "fixtures": [],
            "failingClients": [],
            "healthyClients": [],
        })
        target["occurrences"] += 1
        raw_fixture = str(raw.get("fixture") or "")
        if raw_fixture and raw_fixture not in target["fixtures"]:
            target["fixtures"].append(raw_fixture)
        client = str(raw.get("client") or "unknown").casefold().strip() or "unknown"
        if client not in target["failingClients"]:
            target["failingClients"].append(client)
        for hypothesis in raw.get("hypotheses") or []:
            if not isinstance(hypothesis, dict):
                continue
            hid = str(hypothesis.get("id") or "")
            if hid and hid not in target["hypotheses"]:
                target["hypotheses"].append(hid)

    eligible: list[dict[str, Any]] = []
    compatibility_only: list[dict[str, Any]] = []
    for key, target in grouped.items():
        route_key = key[:3]
        failure_class = key[3]
        healthy_source = (
            extraction_healthy_clients
            if failure_class == "media_extraction_gap"
            else player_healthy_clients
        )
        target["failingClients"] = sorted(set(target["failingClients"]))
        target["healthyClients"] = sorted(healthy_source.get(route_key, set()))
        target["crossClientConfirmed"] = (
            len(target["failingClients"]) >= MIN_DISTINCT_CLIENTS_FOR_GLOBAL_PROVIDER_REPAIR
            and not target["healthyClients"]
        )
        if target["healthyClients"]:
            compatibility_only.append({
                **target,
                "reason": "client_specific_failure_has_healthy_peer",
                "providerMutationAllowed": False,
            })
        elif len(target["failingClients"]) < MIN_DISTINCT_CLIENTS_FOR_GLOBAL_PROVIDER_REPAIR:
            compatibility_only.append({
                **target,
                "reason": "insufficient_cross_client_confirmation",
                "providerMutationAllowed": False,
            })
        else:
            eligible.append(target)

    eligible.sort(key=lambda row: (-int(row["occurrences"]), row["provider"], row["requestType"], row["failureClasses"][0]))
    compatibility_only.sort(key=lambda row: (-int(row["occurrences"]), row["provider"], row["requestType"], row["failureClasses"][0]))

    # Keep at most max_providers distinct providers, while retaining multiple
    # independently corroborated failure/request rows for those providers.
    selected_providers: list[str] = []
    selected: list[dict[str, Any]] = []
    for row in eligible:
        provider = row["provider"]
        if provider not in selected_providers:
            if len(selected_providers) >= max_providers:
                continue
            selected_providers.append(provider)
        selected.append(row)
    return selected, compatibility_only


def skill_memory(learning: dict[str, Any], target: dict[str, Any], skill: str) -> dict[str, int]:
    memory = learning.get("nativeReaderRepairMemory") if isinstance(learning.get("nativeReaderRepairMemory"), dict) else {}
    entries = memory.get("entries") if isinstance(memory.get("entries"), list) else []
    provider = str(target.get("provider") or "").casefold()
    failures = {str(value) for value in target.get("failureClasses") or []}
    fixtures = {str(value) for value in target.get("fixtures") or []}
    matched = [
        row for row in entries
        if isinstance(row, dict)
        and str(row.get("providerId") or "").casefold() == provider
        and str(row.get("skill") or "") == skill
        and (not failures or str(row.get("failureClass") or "") in failures)
        and (not fixtures or str(row.get("fixture") or "") in fixtures)
    ]
    return {
        "attempts": sum(max(0, int(row.get("attempts") or 0)) for row in matched),
        "successes": sum(max(0, int(row.get("successes") or 0)) for row in matched),
        "failures": sum(max(0, int(row.get("failures") or 0)) for row in matched),
        "consecutiveFailures": max([max(0, int(row.get("consecutiveFailures") or 0)) for row in matched] or [0]),
    }


def skills_for(target: dict[str, Any], learning: dict[str, Any], avoid_threshold: int = 2) -> tuple[list[str], list[str]]:
    candidates: list[str] = []
    for hypothesis in target.get("hypotheses") or []:
        for skill in HYPOTHESIS_SKILLS.get(str(hypothesis), ()):
            if skill not in candidates:
                candidates.append(skill)
    ranked: list[tuple[int, int, str]] = []
    suppressed: list[str] = []
    for skill in candidates:
        memory = skill_memory(learning, target, skill)
        if memory["successes"] == 0 and memory["consecutiveFailures"] >= avoid_threshold:
            suppressed.append(skill)
            continue
        ranked.append((-memory["successes"], memory["failures"], skill))
    return [skill for _success, _failures, skill in sorted(ranked)], suppressed


def apply_skill(source: str, skill: str, patch_module) -> str:
    if skill != "global_media_enrichment_v1":
        raise ValueError(f"unsupported reader repair skill: {skill}")
    return patch_module.apply(source, options={
        "max_rows": 12,
        "max_depth": 3,
        "max_candidates": 20,
        "timeout_ms": 9000,
        "default_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--diagnosis", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=ROOT / "manifest.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "native-reader-repair")
    parser.add_argument("--learning-state", type=Path, help="optional prior sanitized Brain learning state")
    parser.add_argument("--fixture", default="", help="optional fixture slug; only its reader failures are considered")
    parser.add_argument("--max-providers", type=int, default=12)
    parser.add_argument("--avoid-threshold", type=int, default=2)
    args = parser.parse_args()

    diagnosis = load_json(args.diagnosis.resolve())
    manifest = load_json(args.manifest.resolve())
    learning = load_optional(args.learning_state.resolve() if args.learning_state else None)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    providers_dir = output_dir / "providers"
    providers_dir.mkdir(parents=True, exist_ok=True)

    target_rows, compatibility_only = diagnosis_targets(
        diagnosis,
        max(1, min(int(args.max_providers), 24)),
        args.fixture.strip() or None,
    )
    by_id = {
        str(row.get("id") or "").casefold(): row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and row.get("id")
    }
    proposed_manifest = copy.deepcopy(manifest)
    proposed_by_id = {
        str(row.get("id") or "").casefold(): row
        for row in proposed_manifest.get("scrapers") or []
        if isinstance(row, dict) and row.get("id")
    }
    patch_module = load_patch_module()
    proposals: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = [dict(row) for row in compatibility_only]

    # Collapse multiple independently corroborated request/failure rows into one
    # provider candidate. Stream-level observations remain intact in the diagnosis;
    # this is only the bounded provider-JS mutation boundary.
    provider_targets: dict[str, dict[str, Any]] = {}
    for target in target_rows:
        provider = target["provider"]
        merged = provider_targets.setdefault(provider, {
            "provider": provider,
            "failureClasses": [],
            "hypotheses": [],
            "occurrences": 0,
            "fixtures": [],
            "requestTypes": [],
            "failingClients": [],
        })
        merged["occurrences"] += int(target.get("occurrences") or 0)
        for field, source in (
            ("failureClasses", target.get("failureClasses") or []),
            ("hypotheses", target.get("hypotheses") or []),
            ("fixtures", target.get("fixtures") or []),
            ("requestTypes", [target.get("requestType")]),
            ("failingClients", target.get("failingClients") or []),
        ):
            for value in source:
                if value and value not in merged[field]:
                    merged[field].append(value)

    for target in sorted(provider_targets.values(), key=lambda row: (-int(row["occurrences"]), row["provider"])):
        provider = target["provider"]
        row = by_id.get(provider)
        proposed_row = proposed_by_id.get(provider)
        skills, suppressed = skills_for(target, learning, max(1, int(args.avoid_threshold)))
        if row is None or proposed_row is None:
            skipped.append({"provider": provider, "reason": "provider_not_in_manifest"})
            continue
        if not skills:
            skipped.append({
                "provider": provider,
                "reason": "all_compatible_reader_skills_suppressed_by_negative_memory" if suppressed else "no_allowlisted_reader_repair_skill",
                "failureClasses": target["failureClasses"],
                "hypotheses": target["hypotheses"],
                "failingClients": target["failingClients"],
                "providerMutationAllowed": False,
                "suppressedSkills": suppressed,
            })
            continue
        try:
            source_path = local_provider_path(str(row.get("filename") or ""))
            original = source_path.read_text(encoding="utf-8")
            repaired = original
            for skill in skills:
                repaired = apply_skill(repaired, skill, patch_module)
        except Exception as error:
            skipped.append({"provider": provider, "reason": f"mutation_error:{type(error).__name__}"})
            continue
        original_bytes = original.encode("utf-8")
        repaired_bytes = repaired.encode("utf-8")
        if repaired_bytes == original_bytes:
            skipped.append({"provider": provider, "reason": "mutation_made_no_change", "skills": skills})
            continue

        digest = sha256(repaired_bytes)
        target_file = providers_dir / f"{safe_fragment(provider)}--brain-reader--{digest[:16]}.js"
        target_file.write_bytes(repaired_bytes)
        relative = target_file.relative_to(ROOT).as_posix()
        proposed_row["filename"] = relative
        proposals.append({
            "provider": provider,
            "fixtures": target["fixtures"],
            "requestTypes": target["requestTypes"],
            "failureClasses": target["failureClasses"],
            "hypotheses": target["hypotheses"],
            "skills": skills,
            "suppressedSkills": suppressed,
            "occurrences": target["occurrences"],
            "failingClients": sorted(target["failingClients"]),
            "crossClientConfirmed": True,
            "sourceSha256": sha256(original_bytes),
            "candidateSha256": digest,
            "candidateFile": relative,
            "requiresFreshNativeReaderProof": True,
        })

    candidate_manifest = output_dir / "manifest.json"
    write_json(candidate_manifest, proposed_manifest)
    diagnosed_reader_failures = int(diagnosis.get("readerFailures") or 0)
    diagnosed_extraction_failures = int(diagnosis.get("extractionFailures") or 0)
    report = {
        "schemaVersion": 3,
        "brainVersion": diagnosis.get("brainVersion"),
        "mode": "native_reader_repair_sandbox",
        "fixtureScope": args.fixture.strip() or "all",
        "diagnosedReaderFailures": diagnosed_reader_failures,
        "diagnosedExtractionFailures": diagnosed_extraction_failures,
        "diagnosedProviderFailures": diagnosed_reader_failures + diagnosed_extraction_failures,
        "proposalCount": len(proposals),
        "providers": [row["provider"] for row in proposals],
        "proposals": proposals,
        "skipped": skipped,
        "compatibilityOnlyCount": len(compatibility_only),
        "learningApplied": bool(learning.get("nativeReaderRepairMemory")),
        "policy": {
            "productionWritesAllowed": False,
            "publicationAllowed": False,
            "candidateManifestOnly": True,
            "requireFreshNativeReaderProof": True,
            "minimumDistinctClientFamiliesForProviderMutation": MIN_DISTINCT_CLIENTS_FOR_GLOBAL_PROVIDER_REPAIR,
            "sameFailureClassCrossClientConsensusRequired": True,
            "healthyPeerVetoesProviderMutation": True,
            "extractionHealthyPeerVetoesExtractionMutation": True,
            "singleClientFailureIsCompatibilityEvidenceOnly": True,
            "maxMutationProviders": max(1, min(int(args.max_providers), 24)),
            "avoidRepeatedFailedSkillThreshold": max(1, int(args.avoid_threshold)),
        },
        "privacy": "No raw media URLs, query tokens, cookie values, authorization values or response-header values are written to this repair report.",
    }
    write_json(output_dir / "repair-report.json", report)
    print(
        f"FIELD_NATIVE_READER_REPAIR proposals={len(proposals)} skipped={len(skipped)} "
        f"compatibility_only={len(compatibility_only)} reader_failures={diagnosed_reader_failures} "
        f"extraction_failures={diagnosed_extraction_failures} fixture={report['fixtureScope']} "
        f"learning={str(report['learningApplied']).lower()} manifest={candidate_manifest.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
