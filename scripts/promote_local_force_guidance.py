#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = ROOT / "automation" / "local-force-results"

ALLOWED_PROFILES = {
    "provider_origin_failover_v1",
    "proven_route_terminal_traversal_v1",
    "chain_terminal_extractor_v1",
    "retained_candidate_replay_v1",
    "player_media_extractor_v1",
    "search_contract_inference_v1",
}

MATERIAL_PROVIDER_INPUTS = {
    "provider-overrides.json",
    "provider_catalog.json",
    "provider-v3-materialization.json",
    "upstream-lkg.json",
}
MATERIAL_PROVIDER_PREFIXES = (
    "providers/",
    "upstream-lkg/",
)


def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid local FORCE guidance: {path}") from exc
    if not isinstance(value, dict):
        raise SystemExit("local FORCE guidance root must be an object")
    return value


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stderr=subprocess.STDOUT,
    ).strip()


def assert_commit(value: str, label: str) -> str:
    sha = str(value or "").strip().casefold()
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise SystemExit(f"{label} must be a full 40-char SHA")
    try:
        git("cat-file", "-e", f"{sha}^{{commit}}")
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"{label} is not available in Git history: {sha}") from exc
    return sha


def provider_materialization_drift(source_sha: str, current_sha: str) -> list[str]:
    try:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", source_sha, current_sha],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            f"local FORCE source SHA is not an ancestor of current SHA: {source_sha} -> {current_sha}"
        ) from exc
    names = [
        line.strip()
        for line in git("diff", "--name-only", source_sha, current_sha, "--").splitlines()
        if line.strip()
    ]
    drift = []
    for name in names:
        if name in MATERIAL_PROVIDER_INPUTS or any(name.startswith(prefix) for prefix in MATERIAL_PROVIDER_PREFIXES):
            drift.append(name)
    return sorted(set(drift))


def latest_guidance() -> Path:
    rows = sorted(DEFAULT_RESULTS.glob("*-winning-guidance.json"))
    if not rows:
        raise SystemExit("no persisted local FORCE winning guidance found")
    return rows[-1]


def validate_row(raw: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "providerId",
        "failureClass",
        "targetLayer",
        "strategy",
        "profile",
        "confidence",
        "priorOnly",
        "experiment",
        "experimentFingerprint",
        "localExperimentSource",
        "guidanceSourceSha",
    }
    if not set(raw).issubset(allowed):
        raise SystemExit(f"unsafe local FORCE guidance row keys: {sorted(set(raw)-allowed)}")
    provider = canon(raw.get("providerId"))
    profile = str(raw.get("profile") or "").strip().casefold()
    target = str(raw.get("targetLayer") or "").strip().casefold()
    fingerprint = str(raw.get("experimentFingerprint") or "").strip().casefold()
    if not provider or target != "provider" or raw.get("priorOnly") is not True:
        raise SystemExit("invalid local FORCE guidance row authority")
    if profile not in ALLOWED_PROFILES:
        raise SystemExit(f"unsupported local FORCE profile: {profile}")
    if not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
        raise SystemExit("invalid local FORCE experiment fingerprint")
    try:
        confidence = float(raw.get("confidence") or 0.0)
    except (TypeError, ValueError) as exc:
        raise SystemExit("invalid local FORCE confidence") from exc
    if confidence < 0.80 or confidence > 1.0:
        raise SystemExit("local FORCE confidence outside safe advisor range")
    experiment = raw.get("experiment")
    if not isinstance(experiment, dict):
        raise SystemExit("local FORCE experiment must be an object")
    return {
        "providerId": provider,
        "failureClass": str(raw.get("failureClass") or "").strip(),
        "targetLayer": "provider",
        "strategy": str(raw.get("strategy") or "").strip(),
        "profile": profile,
        "confidence": confidence,
        "priorOnly": True,
        "experiment": experiment,
        "experimentFingerprint": fingerprint,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path)
    parser.add_argument("--provider", action="append", default=[])
    parser.add_argument("--current-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    targets = []
    seen = set()
    for raw in args.provider:
        provider = canon(raw)
        if provider and provider not in seen:
            seen.add(provider)
            targets.append(provider)
    if not targets:
        raise SystemExit("at least one --provider is required")

    source_path = (args.input or latest_guidance()).resolve()
    value = load_json(source_path)
    if int(value.get("schemaVersion") or 0) != 2:
        raise SystemExit("local FORCE promotion requires schemaVersion=2")
    for key in (
        "publicationAuthority",
        "directMutationAuthority",
        "proofAuthority",
        "rawMutationContentRetained",
        "privateContentRetained",
    ):
        if value.get(key) is not False:
            raise SystemExit(f"unsafe local FORCE authority flag: {key}")

    source_sha = assert_commit(value.get("sourceSha"), "sourceSha")
    current_sha = assert_commit(args.current_sha, "currentSha")
    drift = provider_materialization_drift(source_sha, current_sha)
    if drift:
        raise SystemExit(
            "local FORCE candidate is stale because provider materialization inputs changed: "
            + ",".join(drift)
        )

    rows_by_provider: dict[str, dict[str, Any]] = {}
    for raw in value.get("rows") or []:
        if not isinstance(raw, dict):
            continue
        row = validate_row(raw)
        rows_by_provider[row["providerId"]] = row

    missing = [provider for provider in targets if provider not in rows_by_provider]
    if missing:
        raise SystemExit("requested local FORCE candidate missing: " + ",".join(missing))

    rows = [rows_by_provider[provider] for provider in targets]
    output = {
        "schemaVersion": 2,
        "sourceSha": current_sha,
        "originalLocalForceSourceSha": source_sha,
        "publicationAuthority": False,
        "directMutationAuthority": False,
        "proofAuthority": False,
        "rawMutationContentRetained": False,
        "privateContentRetained": False,
        "priorOnly": True,
        "localForcePromotion": True,
        "providerCount": len(rows),
        "providers": targets,
        "rows": rows,
        "providerMaterializationDrift": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "FIELD_LOCAL_FORCE_PROMOTION "
        f"providers={len(rows)} ids={','.join(targets)} "
        f"source={source_sha} current={current_sha} drift=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
