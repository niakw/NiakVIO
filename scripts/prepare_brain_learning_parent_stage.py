#!/usr/bin/env python3
"""Prepare the executable Learning stage without confusing reconstruction with product state.

The clean reconstruction stage remains the deterministic ProviderBase oracle.
For active providers that do not explicitly require clean reconstruction, Brain
Repair/Learning must mutate the exact currently published bytes instead. This
script copies the reconstruction stage to an isolated execution stage and
overlays only those exact published parent bytes.

No production file is modified and no publication/proof authority is granted.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: JSON object required")
    return data


def rows_by_provider(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in registry.get("candidates") or []:
        if not isinstance(row, dict):
            continue
        provider = canon(row.get("canonical_id") or row.get("upstream_id"))
        if not provider:
            continue
        if provider in rows:
            raise ValueError(f"duplicate candidate provider: {provider}")
        rows[provider] = row
    return rows


def resolve_inside(stage: Path, row: dict[str, Any]) -> Path:
    rel = Path(str(row.get("local_path") or ""))
    if not str(rel) or rel.is_absolute():
        raise ValueError("candidate local_path must be relative")
    path = (stage / rel).resolve()
    path.relative_to(stage.resolve())
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def prepare(
    published_stage: Path,
    reconstruction_stage: Path,
    output_stage: Path,
    providers: list[str] | None = None,
) -> dict[str, Any]:
    published_stage = published_stage.resolve()
    reconstruction_stage = reconstruction_stage.resolve()
    output_stage = output_stage.resolve()

    published_registry = load(published_stage / "candidates.json")
    reconstruction_registry = load(reconstruction_stage / "candidates.json")
    published = rows_by_provider(published_registry)
    reconstruction = rows_by_provider(reconstruction_registry)

    requested = []
    seen: set[str] = set()
    for raw in providers or list(published):
        provider = canon(raw)
        if provider and provider not in seen:
            requested.append(provider)
            seen.add(provider)

    missing = [p for p in requested if p not in published or p not in reconstruction]
    if missing:
        raise ValueError("Learning parent stage missing provider(s): " + ",".join(missing))

    if output_stage.exists():
        shutil.rmtree(output_stage)
    shutil.copytree(reconstruction_stage, output_stage)

    output_registry_path = output_stage / "candidates.json"
    output_registry = load(output_registry_path)
    output_rows = rows_by_provider(output_registry)

    overlaid: list[str] = []
    retained_reconstruction: list[str] = []
    for provider in requested:
        row = output_rows[provider]
        reconstruction_required = row.get("provider_base_reconstruction_required") is True
        original_sha = str(row.get("sha256") or "").strip().casefold()
        if reconstruction_required:
            row["learning_parent_authority"] = "clean-reconstruction-required"
            row["learning_parent_overlay_applied"] = False
            row["learning_parent_proof_authority"] = False
            row["learning_parent_publication_authority"] = False
            retained_reconstruction.append(provider)
            continue

        pub_row = published[provider]
        source = resolve_inside(published_stage, pub_row)
        destination = resolve_inside(output_stage, row)
        exact = source.read_bytes()
        digest = hashlib.sha256(exact).hexdigest()
        declared = str(pub_row.get("sha256") or "").strip().casefold()
        if declared and declared != digest:
            raise ValueError(f"{provider}: published stage digest mismatch")
        destination.write_bytes(exact)

        row["sha256"] = digest
        row["bytes"] = len(exact)
        row["learning_parent_authority"] = "published-exact-current-bytes"
        row["learning_parent_overlay_applied"] = True
        row["learning_parent_published_exact_bytes"] = True
        row["learning_parent_published_key"] = str(pub_row.get("key") or "")
        row["learning_parent_published_sha256"] = digest
        row["learning_reconstruction_sha256"] = original_sha
        row["learning_parent_proof_authority"] = False
        row["learning_parent_publication_authority"] = False
        overlaid.append(provider)

    output_registry["learning_parent_stage"] = {
        "schemaVersion": 1,
        "authority": "published-exact-parent-or-clean-reconstruction-required",
        "requestedProviders": requested,
        "overlaidPublishedExactProviders": overlaid,
        "retainedCleanReconstructionProviders": retained_reconstruction,
        "providerMutationAuthority": False,
        "publicationAuthority": False,
        "proofAuthority": False,
    }
    output_registry_path.write_text(
        json.dumps(output_registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_registry["learning_parent_stage"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--published-stage", type=Path, required=True)
    parser.add_argument("--reconstruction-stage", type=Path, required=True)
    parser.add_argument("--output-stage", type=Path, required=True)
    parser.add_argument("--provider", action="append", default=[])
    args = parser.parse_args()

    report = prepare(
        args.published_stage,
        args.reconstruction_stage,
        args.output_stage,
        args.provider or None,
    )
    registry = load(args.output_stage / "candidates.json")
    rows = rows_by_provider(registry)
    for provider in report["overlaidPublishedExactProviders"]:
        target = resolve_inside(args.output_stage, rows[provider])
        subprocess.run(
            ["node", str(ROOT / "scripts" / "validate_provider_artifact.cjs"), str(target)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    print(
        "FIELD_BRAIN_LEARNING_PARENT_STAGE "
        f"requested={len(report['requestedProviders'])} "
        f"published_exact={len(report['overlaidPublishedExactProviders'])} "
        f"clean_reconstruction={len(report['retainedCleanReconstructionProviders'])} "
        "proof_authority=false publication=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
