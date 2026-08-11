#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get("NUVIO_TV_CANDIDATE_DIR", ROOT / "automation" / "tv-candidates"))
MANIFEST = ROOT / "manifest.json"

PATCHES: dict[str, list[tuple[str, dict[str, Any]]]] = {
    "purstream": [
        ("scripts/provider_patches/purstream_exact_tv_v2.py", {}),
    ],
    "papadustream": [
        ("scripts/provider_patches/papadustream_anime_tv_v1.py", {}),
    ],
    "4khdhubnew": [
        ("scripts/provider_patches/nuvio_tv_playable_first_v1.py", {"max_probes": 6, "timeout_ms": 6500}),
    ],
    "animezey": [
        ("scripts/provider_patches/nuvio_tv_playable_first_v1.py", {"max_probes": 6, "timeout_ms": 6500}),
    ],
    "vegamovies": [
        ("scripts/provider_patches/nuvio_tv_playable_first_v1.py", {"max_probes": 6, "timeout_ms": 6500}),
    ],
    "frenchstream": [
        ("scripts/provider_patches/nuvio_tv_playable_first_v1.py", {"max_probes": 8, "timeout_ms": 6500}),
    ],
    "streamzo": [
        ("scripts/provider_patches/nuvio_tv_playable_first_v1.py", {"max_probes": 8, "timeout_ms": 6500}),
    ],
}


def load_patch(relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(path.stem + "_tv_candidate", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {relative}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "apply"):
        raise RuntimeError(f"missing apply() in {relative}")
    return module.apply


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = {str(row.get("id") or "").casefold(): row for row in manifest.get("scrapers", []) if isinstance(row, dict)}
    OUT.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {"providers": {}}
    for provider_id, chain in PATCHES.items():
        row = rows.get(provider_id)
        if not row:
            raise SystemExit(f"provider missing from manifest: {provider_id}")
        source_path = ROOT / str(row.get("filename") or "")
        if not source_path.is_file():
            raise SystemExit(f"provider file missing: {source_path}")
        source = source_path.read_text(encoding="utf-8")
        markers: list[str] = []
        for relative, options in chain:
            apply = load_patch(relative)
            source = apply(source, options)
            markers.append(Path(relative).stem)
        destination = OUT / f"{provider_id}.js"
        destination.write_text(source, encoding="utf-8")
        report["providers"][provider_id] = {
            "source": source_path.relative_to(ROOT).as_posix(),
            "candidate": destination.relative_to(ROOT).as_posix(),
            "patches": markers,
        }
        print(f"candidate {provider_id}: {source_path.name} -> {destination}")
    (OUT / "candidate-map.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
