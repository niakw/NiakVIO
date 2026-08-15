#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "automation" / "nuvio-tv-compat-v2-report.json"
PATCH = ROOT / "scripts" / "provider_patches" / "nuvio_tv_direct_media_v2.py"
FIXTURE = {
    "tmdbId": "157336",
    "mediaType": "movie",
    "title": "Interstellar",
    "year": 2014,
    "label": "Interstellar (2014)",
    "category": "movie",
    "expectedDurationMinutes": 169,
}
TARGETS: dict[str, dict[str, Any]] = {
    "goated": {"provider_name": "Goated", "max_candidates": 10, "timeout_ms": 12000},
    "wookafr": {
        "provider_name": "Wookafr",
        "strip_unproven_wrappers": True,
        "max_candidates": 12,
        "timeout_ms": 15000,
    },
    "coflix": {"provider_name": "Coflix", "max_candidates": 14, "timeout_ms": 15000},
    "streamzo": {"provider_name": "StreamZo", "max_candidates": 12, "timeout_ms": 15000},
    "frenchstream": {
        "provider_name": "Frenchstream",
        "max_candidates": 12,
        "timeout_ms": 15000,
        "blocked_hosts": ["french-stream.one", "french-stream.club"],
    },
}
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def bump(value: object) -> str:
    match = SEMVER.fullmatch(str(value or ""))
    if not match:
        return "1.0.1"
    major, minor, patch = map(int, match.groups())
    return f"{major}.{minor}.{patch + 1}"


def import_apply(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


def probe(candidate: Path) -> dict[str, Any]:
    env = dict(os.environ)
    env["NODE_OPTIONS"] = "--max-old-space-size=1024"
    try:
        process = subprocess.run(
            [
                "node",
                "scripts/nuvio_tv_probe_v2.cjs",
                str(candidate),
                json.dumps(FIXTURE),
                "{}",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=210,
            env=env,
        )
    except Exception as error:
        return {"ok": False, "error": f"{type(error).__name__}: {error}"}
    parsed: dict[str, Any] | None = None
    for line in reversed(process.stdout.splitlines()):
        try:
            value = json.loads(line.strip())
        except Exception:
            continue
        if isinstance(value, dict):
            parsed = value
            break
    return {
        "ok": bool(parsed and parsed.get("ok") and int(parsed.get("content_verified_count") or 0) > 0 and int(parsed.get("content_verified_count") or 0) == int(parsed.get("playable_stream_count") or 0) and int(parsed.get("identity_contradiction_count") or 0) == 0),
        "returncode": process.returncode,
        "result": parsed,
        "stdout_tail": process.stdout[-5000:],
        "stderr_tail": process.stderr[-4000:],
    }


def vf_filename(value: object) -> str:
    filename = str(value or "")
    if filename.startswith(("http://", "https://", "../")):
        return filename
    return f"../{filename}" if filename.startswith("providers/") else filename


def sync_vf(vf_rows: list[dict[str, Any]], source: dict[str, Any]) -> None:
    canonical = str(source.get("id") or "").casefold()
    target = next((row for row in vf_rows if str(row.get("id") or "").casefold() == canonical), None)
    if target is None:
        target = {}
        vf_rows.append(target)
    target.clear()
    target.update(deepcopy(source))
    target["filename"] = vf_filename(source.get("filename"))


def provenance_update(
    provenance: dict[str, Any], provider_id: str, filename: str, old_sha: str, new_sha: str
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    rows = provenance.setdefault("providers", {})
    row = dict(rows.get(provider_id) or {})
    patches = [str(value) for value in row.get("local_patches") or []]
    patch_path = "scripts/provider_patches/nuvio_tv_direct_media_v2.py"
    if patch_path not in patches:
        patches.append(patch_path)
    row.update(
        {
            "id": provider_id,
            "published_filename": filename,
            "sha256": new_sha,
            "patched_sha256": new_sha,
            "upstream_sha256": row.get("upstream_sha256") or old_sha,
            "local_patches": patches,
            "source": "nuvio-tv-compat-v2",
            "source_name": "Binary-strict NuvioTV direct-media adapter",
            "checked_at": now,
            "check_mode": "nuvio-tv-four-args-binary-strict",
            "check_status": "healthy",
            "activation_eligible": bool(row.get("activation_eligible", False)),
            "strict_activation_eligible": bool(row.get("strict_activation_eligible", False)),
            "runtime_evidence_eligible": bool(row.get("runtime_evidence_eligible", False)),
            "activation_mode": "nuvio_tv_interstellar_binary_proof",
            "activation_blockers": list(row.get("activation_blockers") or []),
        }
    )
    rows[provider_id] = row
    provenance["generated_at"] = now
    provenance["schema_version"] = int(provenance.get("schema_version") or 0) + 1


def main() -> int:
    apply = import_apply(PATCH)
    manifest = load(ROOT / "manifest.json")
    vf = load(ROOT / "vf" / "manifest.json")
    overrides = load(ROOT / "provider-overrides.json")
    provenance = load(ROOT / "PROVENANCE.json")
    main_rows = {
        str(row.get("id") or "").casefold(): row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict)
    }
    vf_rows = [row for row in vf.get("scrapers") or [] if isinstance(row, dict)]
    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fixture": FIXTURE,
        "contract": "NuvioTV 4 positional args; HLS #EXTM3U or binary container proof required",
        "providers": {},
        "published": [],
        "preserved_unresolved": [],
    }

    for provider_id, options in TARGETS.items():
        row = main_rows.get(provider_id)
        if row is None:
            report["providers"][provider_id] = {"ok": False, "error": "manifest row missing"}
            report["preserved_unresolved"].append(provider_id)
            continue
        source_path = ROOT / str(row.get("filename") or "")
        if not source_path.is_file():
            report["providers"][provider_id] = {"ok": False, "error": f"source missing: {source_path}"}
            report["preserved_unresolved"].append(provider_id)
            continue
        source = source_path.read_text(encoding="utf-8", errors="replace")
        patched = apply(source, options)
        sha = hashlib.sha256(patched.encode("utf-8")).hexdigest()
        candidate = ROOT / "staging" / "nuvio-tv-v2" / f"{provider_id}.js"
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_text(patched, encoding="utf-8")
        validation = probe(candidate)
        validation["candidate_sha256"] = sha
        report["providers"][provider_id] = validation
        if not validation.get("ok"):
            report["preserved_unresolved"].append(provider_id)
            continue

        filename = f"providers/{provider_id}--nuvio-tv-v2--{sha[:16]}.js"
        (ROOT / filename).write_text(patched, encoding="utf-8")
        old_filename = str(row.get("filename") or "")
        old_sha = hashlib.sha256(source.encode("utf-8")).hexdigest()
        row["filename"] = filename
        row["version"] = bump(row.get("version"))
        row["enabled"] = row.get("enabled") is True
        row["supportsExternalPlayer"] = False
        sync_vf(vf_rows, row)

        patch_path = "scripts/provider_patches/nuvio_tv_direct_media_v2.py"
        patch = overrides.setdefault("provider_patches", {}).setdefault(provider_id, {})
        scripts = [str(value) for value in patch.get("patch_scripts") or []]
        if patch_path not in scripts:
            scripts.append(patch_path)
        patch["patch_scripts"] = scripts
        patch.setdefault("patch_script_options", {})[patch_path] = options
        patch.setdefault("manifest_overrides", {})["supportsExternalPlayer"] = False
        patch["published_types"] = row.get("supportedTypes", [])
        provenance_update(provenance, provider_id, filename, old_sha, sha)

        result = validation.get("result") or {}
        report["published"].append(
            {
                "id": provider_id,
                "old_filename": old_filename,
                "filename": filename,
                "version": row["version"],
                "raw_stream_count": result.get("raw_stream_count"),
                "playable_stream_count": result.get("playable_stream_count"),
            }
        )

    vf["scrapers"] = vf_rows
    dump(ROOT / "manifest.json", manifest)
    dump(ROOT / "vf" / "manifest.json", vf)
    dump(ROOT / "provider-overrides.json", overrides)
    dump(ROOT / "PROVENANCE.json", provenance)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    dump(REPORT, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["published"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
