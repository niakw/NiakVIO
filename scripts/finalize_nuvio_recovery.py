#!/usr/bin/env python3
"""Finalize a generated Nuvio recovery without touching unrelated providers."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def bump_patch(value: object) -> str:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", str(value or ""))
    if not match:
        return "1.0.1"
    major, minor, patch = map(int, match.groups())
    return f"{major}.{minor}.{patch + 1}"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous", required=True)
    args = parser.parse_args()

    previous = load(Path(args.previous))
    main_path = ROOT / "manifest.json"
    vf_path = ROOT / "vf/manifest.json"
    current = load(main_path)
    vf = load(vf_path)

    previous_rows = {str(row.get("id") or "").casefold(): row for row in previous.get("scrapers", [])}
    current_rows = {str(row.get("id") or "").casefold(): row for row in current.get("scrapers", [])}

    false_positive_rollbacks = {
        "french-manga": "french-manga--nuvio--b088114476c8e08f.js",
        "voiranime-rip": "voiranime-rip--published-baseline--cbf14d7c8fe2e76e.js",
    }

    # The generic repatch is relevant only to active providers that explicitly
    # expose external-player URLs. Revert incidental rewrites of unrelated or
    # disabled bundles so this recovery remains narrowly scoped.
    for provider_id, row in current_rows.items():
        filename = str(row.get("filename") or "")
        if "--repatched--" not in filename:
            continue
        eligible = bool(row.get("enabled")) and bool(row.get("supportsExternalPlayer"))
        if eligible:
            continue
        before = previous_rows.get(provider_id)
        if before:
            row["filename"] = before.get("filename")
            row["version"] = before.get("version")
            row["enabled"] = before.get("enabled")

    # The two previously promoted anime repairs were false positives. Keep the
    # last published baseline disabled until a real anime playback proof exists.
    for provider_id, filename in false_positive_rollbacks.items():
        row = current_rows[provider_id]
        before = previous_rows[provider_id]
        row["filename"] = "providers/" + filename
        row["enabled"] = False
        row["version"] = bump_patch(before.get("version"))

    # Manual Nuvio playback evidence is authoritative for these three entries.
    for provider_id in ("goated", "purstream", "wookafr"):
        current_rows[provider_id]["enabled"] = True
    current_rows["goated"]["version"] = "1.0.1"

    # Mirror changed main-manifest state into the VF manifest.
    vf_rows = {str(row.get("id") or "").casefold(): row for row in vf.get("scrapers", [])}
    synchronized_ids = set(false_positive_rollbacks) | {"goated", "purstream", "wookafr"}
    synchronized_ids.update(
        provider_id
        for provider_id, row in current_rows.items()
        if "--repatched--" in str(row.get("filename") or "")
    )
    for provider_id in synchronized_ids:
        if provider_id not in vf_rows or provider_id not in current_rows:
            continue
        source = current_rows[provider_id]
        target = vf_rows[provider_id]
        target["enabled"] = source.get("enabled")
        target["version"] = source.get("version")
        filename = str(source.get("filename") or "")
        target["filename"] = "../" + filename if filename.startswith("providers/") else filename

    write(main_path, current)
    write(vf_path, vf)

    # Synchronize immutable artifact provenance with the actual manifest. This
    # also repairs the previously stale Wookafr adaptive-repair provenance.
    provenance_path = ROOT / "PROVENANCE.json"
    provenance = load(provenance_path)
    providers = provenance.setdefault("providers", {})
    for provider_id, row in current_rows.items():
        filename = str(row.get("filename") or "")
        target = ROOT / filename
        if not target.is_file():
            raise RuntimeError(f"manifest file missing: {filename}")
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        record = providers.setdefault(provider_id, {"id": provider_id})
        record["published_filename"] = filename
        record["sha256"] = digest
        record["patched_sha256"] = digest
        if "--repatched--" in filename:
            patches = record.setdefault("local_patches", [])
            patch = {
                "type": "patch_script",
                "path": "scripts/provider_patches/stream_output_sanitizer.py",
                "phase": "discovery",
            }
            if patch not in patches:
                patches.append(patch)
    write(provenance_path, provenance)

    # Remove newly generated repatched bundles that are no longer referenced.
    referenced = {
        str(row.get("filename") or "").removeprefix("../")
        for manifest in (current, vf)
        for row in manifest.get("scrapers", [])
    }
    for path in (ROOT / "providers").glob("*--repatched--*.js"):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in referenced:
            path.unlink()

    kept = sorted(
        provider_id
        for provider_id, row in current_rows.items()
        if "--repatched--" in str(row.get("filename") or "")
    )
    print("kept repatched providers:", ", ".join(kept) or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
