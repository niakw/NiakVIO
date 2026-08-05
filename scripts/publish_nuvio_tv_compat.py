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
REPORT = ROOT / "automation" / "nuvio-tv-compat-report.json"
PATCH_PATH = ROOT / "scripts" / "provider_patches" / "nuvio_tv_direct_media.py"
TARGETS: dict[str, dict[str, Any]] = {
    "goated": {"provider_name": "Goated"},
    "wookafr": {"provider_name": "Wookafr"},
    "coflix": {"provider_name": "Coflix"},
    "streamzo": {"provider_name": "StreamZo"},
    "frenchstream": {
        "provider_name": "Frenchstream",
        "blocked_hosts": ["french-stream.one", "french-stream.club"],
    },
}
FIXTURE = {
    "tmdbId": "157336",
    "mediaType": "movie",
    "title": "Interstellar",
    "year": 2014,
    "label": "Interstellar (2014)",
    "category": "movie",
}
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def bump(value: object) -> str:
    match = SEMVER.fullmatch(str(value or ""))
    if not match:
        return "1.0.1"
    major, minor, patch = map(int, match.groups())
    return f"{major}.{minor}.{patch + 1}"


def load_apply(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


def run_probe(path: Path) -> dict[str, Any]:
    env = dict(os.environ)
    env.update({"NODE_OPTIONS": "--max-old-space-size=1024"})
    try:
        process = subprocess.run(
            [
                "node",
                "scripts/nuvio_tv_probe.cjs",
                str(path),
                json.dumps(FIXTURE),
                "{}",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=240,
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
        "ok": bool(parsed and parsed.get("ok") and process.returncode == 0),
        "returncode": process.returncode,
        "result": parsed,
        "stdout_tail": process.stdout[-6000:],
        "stderr_tail": process.stderr[-4000:],
    }


def normalized_vf_filename(filename: object) -> str:
    value = str(filename or "")
    if value.startswith(("http://", "https://", "../")):
        return value
    return f"../{value}" if value.startswith("providers/") else value


def sync_vf_row(vf_rows: list[dict[str, Any]], source: dict[str, Any]) -> dict[str, Any]:
    canonical = str(source.get("id") or "").casefold()
    target = next((row for row in vf_rows if str(row.get("id") or "").casefold() == canonical), None)
    if target is None:
        target = deepcopy(source)
        vf_rows.append(target)
    else:
        target.clear()
        target.update(deepcopy(source))
    target["filename"] = normalized_vf_filename(source.get("filename"))
    return target


def update_provenance(
    provenance: dict[str, Any],
    provider_id: str,
    filename: str,
    old_sha: str,
    new_sha: str,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    providers = provenance.setdefault("providers", {})
    current = dict(providers.get(provider_id) or {})
    patches = [str(value) for value in current.get("local_patches") or []]
    relative_patch = "scripts/provider_patches/nuvio_tv_direct_media.py"
    if relative_patch not in patches:
        patches.append(relative_patch)
    current.update(
        {
            "id": provider_id,
            "published_filename": filename,
            "sha256": new_sha,
            "patched_sha256": new_sha,
            "upstream_sha256": current.get("upstream_sha256") or old_sha,
            "local_patches": patches,
            "source": "nuvio-tv-compat",
            "source_name": "Niakvio strict NuvioTV direct-media compatibility",
            "checked_at": now,
            "check_mode": "nuvio-tv-four-positional-args",
            "check_status": "healthy",
            "activation_eligible": True,
            "strict_activation_eligible": True,
            "runtime_evidence_eligible": True,
            "activation_mode": "nuvio_tv_interstellar_direct_media",
            "activation_blockers": [],
        }
    )
    providers[provider_id] = current
    provenance["generated_at"] = now
    provenance["schema_version"] = int(provenance.get("schema_version") or 0) + 1


def main() -> int:
    apply = load_apply(PATCH_PATH)
    manifest = load(ROOT / "manifest.json")
    vf_manifest = load(ROOT / "vf" / "manifest.json")
    overrides = load(ROOT / "provider-overrides.json")
    provenance = load(ROOT / "PROVENANCE.json")
    main_rows = {
        str(row.get("id") or "").casefold(): row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict)
    }
    vf_rows = [row for row in vf_manifest.get("scrapers") or [] if isinstance(row, dict)]
    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fixture": FIXTURE,
        "contract": "NuvioTV getStreams(tmdbId, mediaType, season, episode) + global SCRAPER_SETTINGS",
        "providers": {},
        "published": [],
    }
    staged: dict[str, dict[str, Any]] = {}

    for provider_id, options in TARGETS.items():
        row = main_rows.get(provider_id)
        if row is None:
            report["providers"][provider_id] = {"ok": False, "error": "missing manifest row"}
            continue
        source_path = ROOT / str(row.get("filename") or "")
        if not source_path.is_file():
            report["providers"][provider_id] = {"ok": False, "error": f"missing source {source_path}"}
            continue
        source = source_path.read_text(encoding="utf-8", errors="replace")
        patched = apply(source, options)
        new_sha = hashlib.sha256(patched.encode("utf-8")).hexdigest()
        candidate = ROOT / "staging" / "nuvio-tv" / f"{provider_id}.js"
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_text(patched, encoding="utf-8")
        probe = run_probe(candidate)
        probe["candidate_sha256"] = new_sha
        report["providers"][provider_id] = probe
        if probe.get("ok"):
            staged[provider_id] = {
                "row": row,
                "source": source,
                "patched": patched,
                "sha": new_sha,
                "candidate": candidate,
                "options": options,
            }

    # Never publish a partial compatibility claim. Existing active providers remain untouched.
    missing = sorted(set(TARGETS) - set(staged))
    if missing:
        report["blocked_publication"] = {"reason": "strict TV proof missing", "providers": missing}
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        dump(REPORT, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    for provider_id, item in staged.items():
        row = item["row"]
        old_filename = str(row.get("filename") or "")
        old_sha = hashlib.sha256(item["source"].encode("utf-8")).hexdigest()
        filename = f"providers/{provider_id}--nuvio-tv--{item['sha'][:16]}.js"
        (ROOT / filename).write_text(item["patched"], encoding="utf-8")
        row["filename"] = filename
        row["version"] = bump(row.get("version"))
        row["enabled"] = True
        row["supportsExternalPlayer"] = False
        sync_vf_row(vf_rows, row)

        patch = overrides.setdefault("provider_patches", {}).setdefault(provider_id, {})
        scripts = [str(value) for value in patch.get("patch_scripts") or []]
        relative_patch = "scripts/provider_patches/nuvio_tv_direct_media.py"
        if relative_patch not in scripts:
            scripts.append(relative_patch)
        patch["patch_scripts"] = scripts
        patch.setdefault("patch_script_options", {})[relative_patch] = item["options"]
        patch.setdefault("manifest_overrides", {})["supportsExternalPlayer"] = False
        patch["published_types"] = row.get("supportedTypes", [])
        update_provenance(provenance, provider_id, filename, old_sha, item["sha"])

        result = report["providers"][provider_id].get("result") or {}
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

    vf_manifest["scrapers"] = vf_rows
    dump(ROOT / "manifest.json", manifest)
    dump(ROOT / "vf" / "manifest.json", vf_manifest)
    dump(ROOT / "provider-overrides.json", overrides)
    dump(ROOT / "PROVENANCE.json", provenance)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    dump(REPORT, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
