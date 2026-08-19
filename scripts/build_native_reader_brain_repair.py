#!/usr/bin/env python3
"""Materialize bounded provider-agnostic repair candidates from native-reader Brain evidence.

This is a Learning Lab mutation step, not publication. It consumes sanitized reader
diagnosis and cross-day reader-repair memory, composes only allow-listed generic
repair skills, writes candidate provider bundles plus a candidate manifest, and
requires a fresh native-reader run before any candidate can be considered successful.
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

HYPOTHESIS_SKILLS: dict[str, tuple[str, ...]] = {
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


def diagnosis_targets(diagnosis: dict[str, Any], max_providers: int, fixture: str | None = None) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    wanted_fixture = str(fixture or "").strip()
    for raw in diagnosis.get("plans") or []:
        if not isinstance(raw, dict):
            continue
        if wanted_fixture and str(raw.get("fixture") or "") != wanted_fixture:
            continue
        provider = str(raw.get("provider") or "").casefold().strip()
        if not provider or str(raw.get("action") or "") != "probe-targeted-repair":
            continue
        target = grouped.setdefault(provider, {
            "provider": provider,
            "failureClasses": [],
            "hypotheses": [],
            "occurrences": 0,
            "fixtures": [],
        })
        target["occurrences"] += 1
        raw_fixture = str(raw.get("fixture") or "")
        if raw_fixture and raw_fixture not in target["fixtures"]:
            target["fixtures"].append(raw_fixture)
        failure = str(raw.get("failureClass") or "unknown_failure")
        if failure not in target["failureClasses"]:
            target["failureClasses"].append(failure)
        for hypothesis in raw.get("hypotheses") or []:
            if not isinstance(hypothesis, dict):
                continue
            hid = str(hypothesis.get("id") or "")
            if hid and hid not in target["hypotheses"]:
                target["hypotheses"].append(hid)
    return sorted(grouped.values(), key=lambda row: (-int(row["occurrences"]), row["provider"]))[:max_providers]


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
    parser.add_argument("--fixture", default="", help="optional fixture slug; only its reader failures are mutated")
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

    target_rows = diagnosis_targets(
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
    skipped: list[dict[str, Any]] = []

    for target in target_rows:
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
            "failureClasses": target["failureClasses"],
            "hypotheses": target["hypotheses"],
            "skills": skills,
            "suppressedSkills": suppressed,
            "occurrences": target["occurrences"],
            "sourceSha256": sha256(original_bytes),
            "candidateSha256": digest,
            "candidateFile": relative,
            "requiresFreshNativeReaderProof": True,
        })

    candidate_manifest = output_dir / "manifest.json"
    write_json(candidate_manifest, proposed_manifest)
    report = {
        "schemaVersion": 2,
        "brainVersion": diagnosis.get("brainVersion"),
        "mode": "native_reader_repair_sandbox",
        "fixtureScope": args.fixture.strip() or "all",
        "diagnosedReaderFailures": int(diagnosis.get("readerFailures") or 0),
        "proposalCount": len(proposals),
        "providers": [row["provider"] for row in proposals],
        "proposals": proposals,
        "skipped": skipped,
        "learningApplied": bool(learning.get("nativeReaderRepairMemory")),
        "policy": {
            "productionWritesAllowed": False,
            "publicationAllowed": False,
            "candidateManifestOnly": True,
            "requireFreshNativeReaderProof": True,
            "maxMutationProviders": max(1, min(int(args.max_providers), 24)),
            "avoidRepeatedFailedSkillThreshold": max(1, int(args.avoid_threshold)),
        },
        "privacy": "No raw media URLs, query tokens, cookie values, authorization values or response-header values are written to this repair report.",
    }
    write_json(output_dir / "repair-report.json", report)
    print(
        f"FIELD_NATIVE_READER_REPAIR proposals={len(proposals)} skipped={len(skipped)} "
        f"reader_failures={report['diagnosedReaderFailures']} fixture={report['fixtureScope']} learning={str(report['learningApplied']).lower()} manifest={candidate_manifest.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
