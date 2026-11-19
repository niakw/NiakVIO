#!/usr/bin/env python3
"""Source-pinned ephemeral ProviderBase candidate; never a published/Brain repair."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = "NIAKVIO_PROVIDER_NATIVE_PLAYER_HEDGE_V27"
# Additional causal signatures are only source-owned generic Core/ProviderBase
# mechanisms. The caller cannot substitute provider-specific executable code.
REQUIRED_MARKERS = {
    "",
    "NIAKVIO_HLS_TS_WRAPPED_AAC_RENDITION_V20",
    "NIAKVIO_PROVIDER_NATIVE_FETCH_CAPABILITY_GATE_V28",
}


def rows(manifest: Path, provider: str) -> tuple[dict, int]:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    seen: set[str] = set()
    index = 0
    for row in data.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        name, filename = str(row.get("id") or "").strip().lower(), str(row.get("filename") or "").strip()
        if not name or not filename or name in seen:
            continue
        seen.add(name)
        if name == provider:
            if row.get("enabled") is not True:
                raise ValueError("candidate provider must be active")
            return row, index
        index += 1
    raise ValueError("candidate provider absent from selected manifest")


def js_path(manifest: Path, row: dict) -> Path:
    filename = str(row.get("filename") or "")
    if filename.startswith(("http://", "https://")):
        raise ValueError("candidate filename must be local")
    path = (manifest.parent / filename).resolve()
    relative = path.relative_to(ROOT)
    if not relative.parts or relative.parts[0] != "providers" or path.suffix != ".js" or not path.is_file():
        raise ValueError("candidate JS must be a local active provider")
    return path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--provider", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--source-sha", default="")
    p.add_argument("--output", default="automation/native-candidate-remat-proof.json")
    p.add_argument("--verify-staging", action="store_true")
    p.add_argument("--client-root", default="")
    p.add_argument("--required-marker", default="")
    args = p.parse_args()

    required_marker = args.required_marker.strip()
    if required_marker not in REQUIRED_MARKERS:
        raise ValueError("unsupported source-owned native candidate marker")
    provider = args.provider.strip().lower()
    if not re.fullmatch(r"[a-z][a-z0-9-]{1,79}", provider):
        raise ValueError("invalid provider")
    manifest = (ROOT / args.manifest).resolve()
    if manifest not in {(ROOT / "manifest.json").resolve(), (ROOT / "vf/manifest.json").resolve()}:
        raise ValueError("unsupported manifest projection")
    output = (ROOT / args.output).resolve()
    output.relative_to(ROOT)
    row, index = rows(manifest, provider)
    local_js = js_path(manifest, row)

    if args.verify_staging:
        proof = json.loads(output.read_text(encoding="utf-8"))
        if (
            proof.get("provider") != provider
            or proof.get("manifest") != args.manifest
            or proof.get("requiredCoreMarker", "") != required_marker
        ):
            raise ValueError("candidate provenance mismatch")
        candidate_sha = str(proof.get("candidateJsSha256") or "")
        if not re.fullmatch(r"[a-f0-9]{64}", candidate_sha) or sha256(local_js) != candidate_sha:
            raise ValueError("candidate source bytes diverged")
        if required_marker and required_marker not in local_js.read_text(encoding="utf-8"):
            raise ValueError("required generic Core marker absent from staged candidate source")
        if not args.client_root:
            raise ValueError("official client checkout required")
        # The native stage filters to NIAKVIO_PROVIDER_SCOPE_MATRIX *before*
        # assigning pNNN.js indexes. The single-provider candidate must be p000.
        scope_raw = os.environ.get("NIAKVIO_PROVIDER_SCOPE_MATRIX", "").strip()
        if not scope_raw:
            raise ValueError("candidate requires exact native provider scope")
        scope_path = Path(scope_raw).resolve()
        scope_path.relative_to(ROOT)
        scope = json.loads(scope_path.read_text(encoding="utf-8"))
        stage_ids = [str(v.get("manifestId") or v.get("provider") or "").strip().lower()
                     for v in scope.get("rows") or [] if isinstance(v, dict)]
        if stage_ids != [provider] or int(scope.get("providerCount") or 0) != 1:
            raise ValueError("candidate staging scope must contain exactly the requested provider")
        asset = Path(args.client_root).resolve() / "app/src/androidTest/assets/niakvio/p000.js"
        if not asset.is_file() or sha256(asset) != candidate_sha:
            raise ValueError("candidate bytes not actually staged in official NuvioTV test")
        proof["officialTvTestAssetByteMatched"] = True
        proof["productionPlaybackVerified"] = False
        proof["publicationAllowed"] = False
        write(output, proof)
        print(f"FIELD_NATIVE_CANDIDATE_STAGED provider={provider} sha256={candidate_sha} matched=true publication=false", flush=True)
        return

    source_sha = args.source_sha.strip().lower()
    actual_source = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip().lower()
    if not re.fullmatch(r"[a-f0-9]{40}", source_sha) or source_sha != actual_source:
        raise ValueError("candidate requires exact source checkout SHA")
    if os.environ.get("NUVIO_PROVIDER_V3_CONTEXT") != "workspace":
        raise ValueError("candidate requires ephemeral workspace materialization")
    baseline_sha = sha256(local_js)
    subprocess.run([sys.executable, "scripts/materialize_provider_v3_one.py", provider], cwd=ROOT, check=True, timeout=240)
    updated_row, _ = rows(manifest, provider)
    candidate_path = js_path(manifest, updated_row)
    candidate_sha = sha256(candidate_path)
    candidate_source = candidate_path.read_text(encoding="utf-8")
    if candidate_sha == baseline_sha or MARKER not in candidate_source:
        raise ValueError("candidate did not rematerialize changed ProviderBase bytes")
    if required_marker and required_marker not in candidate_source:
        raise ValueError("candidate did not materialize required source-owned Core marker")
    proof = {
        "schemaVersion": 1, "provider": provider, "manifest": args.manifest,
        "sourceNiakvioSha": source_sha, "publishedBaselineJsSha256": baseline_sha,
        "candidateJsSha256": candidate_sha, "candidateByteChanged": True,
        "requiredCoreMarker": required_marker,
        "generatedByBrain": False, "generatedByProviderBase": True,
        "officialTvTestAssetByteMatched": False, "productionPlaybackVerified": False,
        "publicationAllowed": False,
    }
    write(output, proof)
    print(f"FIELD_NATIVE_CANDIDATE_REMAT provider={provider} from={baseline_sha} to={candidate_sha} marker=true publication=false", flush=True)


if __name__ == "__main__":
    main()
