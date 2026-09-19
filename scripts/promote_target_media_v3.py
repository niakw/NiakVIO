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
PATCH_PATH = ROOT / "scripts" / "provider_patches" / "nuvio_tv_target_media_v3.py"
REPORT_PATH = ROOT / "automation" / "nuvio-tv-target-media-v3.json"
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
TARGETS: dict[str, dict[str, Any]] = {
    "wookafr": {"provider_name": "Wookafr", "max_candidates": 20, "timeout_ms": 20000},
    "coflix": {"provider_name": "Coflix", "max_candidates": 22, "timeout_ms": 20000},
    "frenchstream": {"provider_name": "Frenchstream", "max_candidates": 22, "timeout_ms": 20000},
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def import_apply(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


def bump(value: object) -> str:
    match = SEMVER.fullmatch(str(value or ""))
    if not match:
        return "1.0.1"
    major, minor, patch = map(int, match.groups())
    return f"{major}.{minor}.{patch + 1}"


def first_fixture(config: dict[str, Any], category: str) -> dict[str, Any]:
    rows = config.get("fixtures", {}).get(category, [])
    if not rows:
        raise RuntimeError(f"missing fixture {category}")
    fixture = dict(rows[0])
    fixture.setdefault("category", category)
    return fixture


def fixtures_for(row: dict[str, Any], health: dict[str, Any]) -> list[dict[str, Any]]:
    supported = {
        str(value).strip().casefold()
        for value in (row.get("supportedTypes") or row.get("types") or [])
        if str(value).strip()
    }
    categories: list[str] = []
    if "movie" in supported or not supported:
        categories.append("movie")
    if "tv" in supported:
        categories.append("tv")
    if "anime" in supported:
        categories.append("anime")
    return [first_fixture(health, category) for category in categories[:3]]


def parse_probe(stdout: str) -> dict[str, Any] | None:
    for line in reversed(stdout.splitlines()):
        try:
            value = json.loads(line.strip())
        except Exception:
            continue
        if isinstance(value, dict) and "playable_stream_count" in value:
            return value
    return None


def probe(path: Path, fixture: dict[str, Any], timeout_seconds: int = 210) -> dict[str, Any]:
    env = dict(os.environ)
    env["NODE_OPTIONS"] = "--max-old-space-size=1024"
    try:
        process = subprocess.run(
            [
                "node", "scripts/nuvio_tv_probe_v2.cjs", str(path),
                json.dumps(fixture, ensure_ascii=False), "{}",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=env,
        )
    except Exception as error:
        return {"ok": False, "returncode": 1, "result": None, "error": f"{type(error).__name__}: {error}"}
    parsed = parse_probe(process.stdout)
    return {
        "ok": bool(parsed and parsed.get("ok") and int(parsed.get("content_verified_count") or 0) > 0 and int(parsed.get("content_verified_count") or 0) == int(parsed.get("playable_stream_count") or 0) and int(parsed.get("identity_contradiction_count") or 0) == 0),
        "returncode": process.returncode,
        "result": parsed,
        "stdout_tail": process.stdout[-6000:],
        "stderr_tail": process.stderr[-3000:],
    }


def score(value: dict[str, Any]) -> tuple[int, int]:
    result = value.get("result") or {}
    playable = int(result.get("playable_stream_count") or 0)
    verified = int(result.get("content_verified_count") or result.get("identity_verified_count") or 0)
    contradictions = int(result.get("identity_contradiction_count") or 0)
    strict = playable > 0 and verified == playable and contradictions == 0
    return (1 if strict else 0, verified if strict else 0)


def strict_item(item: dict[str, Any]) -> bool:
    media = item.get("media") if isinstance(item.get("media"), dict) else {}
    return bool(
        media.get("playable")
        and not media.get("error")
        and (media.get("starts_extm3u") or media.get("binary_signature") or media.get("kind") == "dash")
    )


def validate(source: Path, candidate: Path, fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    baseline: list[dict[str, Any]] = []
    patched: list[dict[str, Any]] = []
    for fixture in fixtures:
        baseline.append({"fixture": fixture, **probe(source, fixture)})
        patched.append({"fixture": fixture, **probe(candidate, fixture)})
    before = (sum(score(row)[0] for row in baseline), sum(score(row)[1] for row in baseline))
    after = (sum(score(row)[0] for row in patched), sum(score(row)[1] for row in patched))
    no_regression = all(score(new)[0] >= score(old)[0] for old, new in zip(baseline, patched))
    strict_outputs = True
    for row in patched:
        for item in (row.get("result") or {}).get("streams") or []:
            media = item.get("media") if isinstance(item, dict) else None
            if media and media.get("playable") and not strict_item(item):
                strict_outputs = False
    return {
        "baseline": baseline,
        "candidate": patched,
        "baseline_summary": {"playable_fixture_count": before[0], "playable_stream_count": before[1]},
        "candidate_summary": {"playable_fixture_count": after[0], "playable_stream_count": after[1]},
        "no_regression": no_regression,
        "strict_outputs": strict_outputs,
        "strictly_better": no_regression and strict_outputs and after > before,
    }


def vf_filename(value: object) -> str:
    filename = str(value or "")
    if filename.startswith(("../", "http://", "https://")):
        return filename
    return f"../{filename}" if filename.startswith("providers/") else filename


def sync_vf(rows: list[dict[str, Any]], source: dict[str, Any]) -> None:
    provider_id = str(source.get("id") or "").casefold()
    target = next((row for row in rows if str(row.get("id") or "").casefold() == provider_id), None)
    if target is None:
        target = {}
        rows.append(target)
    target.clear()
    target.update(deepcopy(source))
    target["filename"] = vf_filename(source.get("filename"))


def update_provenance(
    provenance: dict[str, Any], provider_id: str, filename: str, old_sha: str, new_sha: str
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    rows = provenance.setdefault("providers", {})
    current = dict(rows.get(provider_id) or rows.get(provider_id.upper()) or {})
    patch_path = "scripts/provider_patches/nuvio_tv_target_media_v3.py"
    patches = [str(value) for value in current.get("local_patches") or []]
    if patch_path not in patches:
        patches.append(patch_path)
    current.update(
        {
            "id": provider_id,
            "published_filename": filename,
            "sha256": new_sha,
            "patched_sha256": new_sha,
            "upstream_sha256": current.get("upstream_sha256") or old_sha,
            "local_patches": patches,
            "source": "target-media-v3",
            "source_name": "Strict LecteurVideo/MegaUp/Vidzy media resolution",
            "checked_at": now,
            "check_mode": "nuvio-tv-target-player-chain",
            "check_status": "healthy",
            "activation_eligible": bool(current.get("activation_eligible", False)),
            "strict_activation_eligible": bool(current.get("strict_activation_eligible", False)),
            "runtime_evidence_eligible": bool(current.get("runtime_evidence_eligible", False)),
            "activation_mode": "target_media_v3",
            "activation_blockers": list(current.get("activation_blockers") or []),
        }
    )
    rows[provider_id] = current
    provenance["generated_at"] = now
    provenance["schema_version"] = int(provenance.get("schema_version") or 0) + 1


def main() -> int:
    apply = import_apply(PATCH_PATH)
    manifest = load(ROOT / "manifest.json")
    vf_manifest = load(ROOT / "vf" / "manifest.json")
    overrides = load(ROOT / "provider-overrides.json")
    provenance = load(ROOT / "PROVENANCE.json")
    health = load(ROOT / "health-config.json")
    main_rows = {
        str(row.get("id") or "").casefold(): row
        for row in manifest.get("scrapers") or [] if isinstance(row, dict)
    }
    vf_rows = [row for row in vf_manifest.get("scrapers") or [] if isinstance(row, dict)]
    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "contract": "NuvioTV four positional arguments and global SCRAPER_SETTINGS",
        "media_gate": "#EXTM3U, DASH MPD, or real video container signature",
        "providers": {},
        "published": [],
        "preserved": [],
    }

    for provider_id, options in TARGETS.items():
        row = main_rows.get(provider_id)
        if row is None:
            report["providers"][provider_id] = {"ok": False, "error": "manifest row missing"}
            report["preserved"].append(provider_id)
            continue
        source_path = ROOT / str(row.get("filename") or "")
        if not source_path.is_file():
            report["providers"][provider_id] = {"ok": False, "error": f"missing {source_path}"}
            report["preserved"].append(provider_id)
            continue
        source = source_path.read_text(encoding="utf-8", errors="replace")
        patched = apply(source, options)
        sha = hashlib.sha256(patched.encode("utf-8")).hexdigest()
        candidate = ROOT / "staging" / "target-media-v3" / f"{provider_id}--{sha[:16]}.js"
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_text(patched, encoding="utf-8")
        validation = validate(source_path, candidate, fixtures_for(row, health))
        validation["candidate_sha256"] = sha
        validation["options"] = options
        report["providers"][provider_id] = validation
        if not validation.get("strictly_better"):
            report["preserved"].append(provider_id)
            continue

        old_sha = hashlib.sha256(source.encode("utf-8")).hexdigest()
        filename = f"providers/{provider_id}--target-media-v3--{sha[:16]}.js"
        (ROOT / filename).write_text(patched, encoding="utf-8")
        old_filename = str(row.get("filename") or "")
        row["filename"] = filename
        row["version"] = bump(row.get("version"))
        row["enabled"] = row.get("enabled") is True
        row["supportsExternalPlayer"] = False
        sync_vf(vf_rows, row)

        patch_path = "scripts/provider_patches/nuvio_tv_target_media_v3.py"
        patch = overrides.setdefault("provider_patches", {}).setdefault(provider_id, {})
        scripts = [str(value) for value in patch.get("patch_scripts") or []]
        if patch_path not in scripts:
            scripts.append(patch_path)
        patch["patch_scripts"] = scripts
        patch.setdefault("patch_script_options", {})[patch_path] = options
        patch.setdefault("manifest_overrides", {})["supportsExternalPlayer"] = False
        patch["published_types"] = row.get("supportedTypes", [])
        update_provenance(provenance, provider_id, filename, old_sha, sha)
        report["published"].append(
            {
                "id": provider_id,
                "old_filename": old_filename,
                "filename": filename,
                "version": row["version"],
                "candidate_summary": validation["candidate_summary"],
            }
        )

    vf_manifest["scrapers"] = vf_rows
    dump(ROOT / "manifest.json", manifest)
    dump(ROOT / "vf" / "manifest.json", vf_manifest)
    dump(ROOT / "provider-overrides.json", overrides)
    dump(ROOT / "PROVENANCE.json", provenance)
    dump(REPORT_PATH, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
