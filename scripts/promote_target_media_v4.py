#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import promote_target_media_v3 as promotion

ROOT = Path(__file__).resolve().parents[1]
V3_PATCH = "scripts/provider_patches/nuvio_tv_target_media_v3.py"
V4_PATCH = "scripts/provider_patches/nuvio_tv_target_media_v4.py"
BLOCKED_AD_HOSTS = [
    "snap.com",
    "snapchat.com",
    "ctfassets.net",
    "sc-cdn.net",
]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def replace_patch_path(values: object) -> list[str]:
    result: list[str] = []
    for value in values if isinstance(values, list) else []:
        item = V4_PATCH if str(value) == V3_PATCH else str(value)
        if item not in result:
            result.append(item)
    if V4_PATCH not in result:
        result.append(V4_PATCH)
    return result


def finalize_metadata() -> None:
    manifest_path = ROOT / "manifest.json"
    vf_path = ROOT / "vf" / "manifest.json"
    overrides_path = ROOT / "provider-overrides.json"
    provenance_path = ROOT / "PROVENANCE.json"
    report_path = promotion.REPORT_PATH

    manifest = load(manifest_path)
    vf_manifest = load(vf_path)
    overrides = load(overrides_path)
    provenance = load(provenance_path)
    report = load(report_path)

    published_ids = {str(row.get("id") or "").casefold() for row in report.get("published", [])}
    if "frenchstream" not in published_ids:
        dump(report_path, report)
        return

    main_rows = {
        str(row.get("id") or "").casefold(): row
        for row in manifest.get("scrapers", [])
        if isinstance(row, dict)
    }
    row = main_rows["frenchstream"]
    old_filename = str(row.get("filename") or "")
    source_path = ROOT / old_filename
    if "--target-media-v3--" in old_filename and source_path.is_file():
        new_filename = old_filename.replace("--target-media-v3--", "--target-media-v4--")
        target_path = ROOT / new_filename
        source_path.replace(target_path)
        row["filename"] = new_filename
        for vf_row in vf_manifest.get("scrapers", []):
            if str(vf_row.get("id") or "").casefold() == "frenchstream":
                vf_row["filename"] = f"../{new_filename}"
        for published in report.get("published", []):
            if str(published.get("id") or "").casefold() == "frenchstream":
                published["filename"] = new_filename

    patch = overrides.setdefault("provider_patches", {}).setdefault("frenchstream", {})
    patch["patch_scripts"] = replace_patch_path(patch.get("patch_scripts"))
    options = patch.setdefault("patch_script_options", {})
    options.pop(V3_PATCH, None)
    options[V4_PATCH] = dict(promotion.TARGETS["frenchstream"])

    provenance_rows = provenance.setdefault("providers", {})
    current = dict(provenance_rows.get("frenchstream") or provenance_rows.get("FRENCHSTREAM") or {})
    current["published_filename"] = row["filename"]
    current["local_patches"] = replace_patch_path(current.get("local_patches"))
    current["source"] = "target-media-v4"
    current["source_name"] = "Strict target media resolution with provenance filtering"
    current["activation_mode"] = "target_media_v4"
    provenance_rows["frenchstream"] = current

    report["resolver_version"] = "v4"
    report["blocked_unrelated_media_hosts"] = BLOCKED_AD_HOSTS

    dump(manifest_path, manifest)
    dump(vf_path, vf_manifest)
    dump(overrides_path, overrides)
    dump(provenance_path, provenance)
    dump(report_path, report)


def main() -> int:
    promotion.PATCH_PATH = ROOT / V4_PATCH
    promotion.TARGETS["frenchstream"] = {
        **promotion.TARGETS["frenchstream"],
        "blocked_hosts": BLOCKED_AD_HOSTS,
    }
    status = promotion.main()
    finalize_metadata()
    return status


if __name__ == "__main__":
    raise SystemExit(main())
