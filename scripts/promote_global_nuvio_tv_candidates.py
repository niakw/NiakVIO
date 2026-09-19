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
PATCH_PATH = ROOT / "scripts" / "provider_patches" / "nuvio_tv_direct_media_v2.py"
REPORT_PATH = ROOT / "automation" / "nuvio-tv-global-promotion.json"
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
TARGETS: dict[str, dict[str, Any]] = {
    "desiflix": {
        "provider_name": "DesiFlix",
        "max_candidates": 14,
        "timeout_ms": 14000,
    },
    "french-manga": {
        "provider_name": "French-Manga",
        "max_candidates": 14,
        "timeout_ms": 14000,
        "strip_unproven_wrappers": True,
    },
    "streamzo": {
        "provider_name": "StreamZo",
        "max_candidates": 14,
        "timeout_ms": 14000,
    },
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
        raise RuntimeError(f"missing fixture category: {category}")
    result = dict(rows[0])
    result.setdefault("category", category)
    return result


def fixtures_for(row: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    supported = {
        str(value).strip().casefold()
        for value in (row.get("supportedTypes") or row.get("types") or [])
        if str(value).strip()
    }
    identity = " ".join(str(row.get(key) or "") for key in ("id", "name", "description"))
    categories: list[str] = []
    if "movie" in supported:
        categories.append("movie")
    if "tv" in supported:
        categories.append("tv")
    if "anime" in supported:
        categories.append("anime")
    if not categories:
        categories.append("anime" if re.search(r"anime|manga|vost", identity, re.I) else "movie")
    if re.search(r"anime|manga|vost", identity, re.I) and "anime" not in categories and "tv" in supported:
        categories.append("anime")
    fixtures: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for category in categories:
        fixture = first_fixture(config, category)
        key = (
            fixture.get("tmdbId"), fixture.get("mediaType"), fixture.get("season"),
            fixture.get("episode"), category,
        )
        if key not in seen:
            seen.add(key)
            fixtures.append(fixture)
    return fixtures[:3]


def parse_probe(stdout: str) -> dict[str, Any] | None:
    for line in reversed(stdout.splitlines()):
        try:
            value = json.loads(line.strip())
        except Exception:
            continue
        if isinstance(value, dict) and "playable_stream_count" in value:
            return value
    return None


def probe(path: Path, fixture: dict[str, Any], timeout_seconds: int = 150) -> dict[str, Any]:
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
        return {
            "ok": False,
            "returncode": 1,
            "result": None,
            "error": f"{type(error).__name__}: {error}",
        }
    parsed = parse_probe(process.stdout)
    return {
        "ok": bool(parsed and parsed.get("ok") and int(parsed.get("content_verified_count") or 0) > 0 and int(parsed.get("content_verified_count") or 0) == int(parsed.get("playable_stream_count") or 0) and int(parsed.get("identity_contradiction_count") or 0) == 0),
        "returncode": process.returncode,
        "result": parsed,
        "stdout_tail": process.stdout[-5000:],
        "stderr_tail": process.stderr[-2500:],
    }


def score(result: dict[str, Any]) -> tuple[int, int]:
    value = result.get("result") or {}
    playable = int(value.get("playable_stream_count") or 0)
    verified = int(value.get("content_verified_count") or value.get("identity_verified_count") or 0)
    contradictions = int(value.get("identity_contradiction_count") or 0)
    strict = playable > 0 and verified == playable and contradictions == 0
    return (1 if strict else 0, verified if strict else 0)


def media_is_strict(item: dict[str, Any]) -> bool:
    media = item.get("media") if isinstance(item.get("media"), dict) else {}
    return bool(
        media.get("playable")
        and not media.get("error")
        and (
            media.get("starts_extm3u")
            or media.get("binary_signature")
            or media.get("kind") == "dash"
        )
    )


def validate_candidate(
    baseline_path: Path,
    candidate_path: Path,
    fixtures: list[dict[str, Any]],
) -> dict[str, Any]:
    baseline: list[dict[str, Any]] = []
    candidate: list[dict[str, Any]] = []
    for fixture in fixtures:
        before = probe(baseline_path, fixture)
        after = probe(candidate_path, fixture)
        baseline.append({"fixture": fixture, **before})
        candidate.append({"fixture": fixture, **after})

    no_regression = all(score(after) >= (score(before)[0], 0) for before, after in zip(baseline, candidate))
    before_summary = (
        sum(score(item)[0] for item in baseline),
        sum(score(item)[1] for item in baseline),
    )
    after_summary = (
        sum(score(item)[0] for item in candidate),
        sum(score(item)[1] for item in candidate),
    )
    strict_outputs = True
    for result in candidate:
        parsed = result.get("result") or {}
        for item in parsed.get("streams") or []:
            media = item.get("media") if isinstance(item, dict) else None
            if media and media.get("playable") and not media_is_strict(item):
                strict_outputs = False

    return {
        "baseline": baseline,
        "candidate": candidate,
        "baseline_summary": {
            "playable_fixture_count": before_summary[0],
            "playable_stream_count": before_summary[1],
        },
        "candidate_summary": {
            "playable_fixture_count": after_summary[0],
            "playable_stream_count": after_summary[1],
        },
        "no_regression": no_regression,
        "strict_outputs": strict_outputs,
        "strictly_better": no_regression and strict_outputs and after_summary > before_summary,
    }


def vf_filename(value: object) -> str:
    filename = str(value or "")
    if filename.startswith(("../", "http://", "https://")):
        return filename
    return f"../{filename}" if filename.startswith("providers/") else filename


def sync_vf(vf_rows: list[dict[str, Any]], source: dict[str, Any]) -> None:
    provider_id = str(source.get("id") or "").casefold()
    target = next((row for row in vf_rows if str(row.get("id") or "").casefold() == provider_id), None)
    if target is None:
        target = {}
        vf_rows.append(target)
    target.clear()
    target.update(deepcopy(source))
    target["filename"] = vf_filename(source.get("filename"))


def update_provenance(
    provenance: dict[str, Any], provider_id: str, filename: str, old_sha: str, new_sha: str
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    rows = provenance.setdefault("providers", {})
    row = dict(rows.get(provider_id) or rows.get(provider_id.upper()) or {})
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
            "source": "global-nuvio-tv-audit-v2",
            "source_name": "Strict global NuvioTV media audit",
            "checked_at": now,
            "check_mode": "all-declared-types-strict-media-proof",
            "check_status": "healthy",
            "activation_eligible": bool(row.get("activation_eligible", False)),
            "strict_activation_eligible": bool(row.get("strict_activation_eligible", False)),
            "runtime_evidence_eligible": bool(row.get("runtime_evidence_eligible", False)),
            "activation_mode": "global_strict_tv_promotion",
            "activation_blockers": list(row.get("activation_blockers") or []),
        }
    )
    rows[provider_id] = row
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
        "contract": "NuvioTV four positional args plus global SCRAPER_SETTINGS",
        "media_gate": "#EXTM3U, DASH MPD, or real video container signature",
        "providers": {},
        "published": [],
        "preserved": [],
    }

    for canonical, options in TARGETS.items():
        row = main_rows.get(canonical)
        if row is None:
            report["providers"][canonical] = {"ok": False, "error": "manifest row missing"}
            report["preserved"].append(canonical)
            continue
        source_path = ROOT / str(row.get("filename") or "")
        if not source_path.is_file():
            report["providers"][canonical] = {"ok": False, "error": f"missing {source_path}"}
            report["preserved"].append(canonical)
            continue
        source = source_path.read_text(encoding="utf-8", errors="replace")
        patched = apply(source, options)
        new_sha = hashlib.sha256(patched.encode("utf-8")).hexdigest()
        candidate_path = ROOT / "staging" / "global-tv-promotion" / f"{canonical}--{new_sha[:16]}.js"
        candidate_path.parent.mkdir(parents=True, exist_ok=True)
        candidate_path.write_text(patched, encoding="utf-8")
        fixtures = fixtures_for(row, health)
        validation = validate_candidate(source_path, candidate_path, fixtures)
        validation["candidate_sha256"] = new_sha
        validation["options"] = options
        report["providers"][canonical] = validation
        if not validation.get("strictly_better"):
            report["preserved"].append(canonical)
            continue

        old_sha = hashlib.sha256(source.encode("utf-8")).hexdigest()
        filename = f"providers/{canonical}--nuvio-tv-global--{new_sha[:16]}.js"
        (ROOT / filename).write_text(patched, encoding="utf-8")
        old_filename = str(row.get("filename") or "")
        row["filename"] = filename
        row["version"] = bump(row.get("version"))
        row["enabled"] = row.get("enabled") is True
        row["supportsExternalPlayer"] = False
        sync_vf(vf_rows, row)

        patch_path = "scripts/provider_patches/nuvio_tv_direct_media_v2.py"
        patch = overrides.setdefault("provider_patches", {}).setdefault(canonical, {})
        scripts = [str(value) for value in patch.get("patch_scripts") or []]
        if patch_path not in scripts:
            scripts.append(patch_path)
        patch["patch_scripts"] = scripts
        patch.setdefault("patch_script_options", {})[patch_path] = options
        patch.setdefault("manifest_overrides", {})["supportsExternalPlayer"] = False
        patch["published_types"] = row.get("supportedTypes", [])
        update_provenance(provenance, canonical, filename, old_sha, new_sha)
        report["published"].append(
            {
                "id": canonical,
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
    return 0 if report["published"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
