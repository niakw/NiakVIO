#!/usr/bin/env python3
"""Remove residual repatched files no longer selected by the main manifest."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
main_path = ROOT / "manifest.json"
vf_path = ROOT / "vf/manifest.json"
main = json.loads(main_path.read_text(encoding="utf-8"))
vf = json.loads(vf_path.read_text(encoding="utf-8"))
main_rows = {str(row.get("id") or "").casefold(): row for row in main.get("scrapers", [])}

for row in vf.get("scrapers", []):
    provider_id = str(row.get("id") or "").casefold()
    filename = str(row.get("filename") or "")
    source = main_rows.get(provider_id)
    if source is None or "--repatched--" not in filename:
        continue
    main_filename = str(source.get("filename") or "")
    row["filename"] = "../" + main_filename if main_filename.startswith("providers/") else main_filename
    row["version"] = source.get("version")
    row["enabled"] = source.get("enabled")

vf_path.write_text(json.dumps(vf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

referenced = {
    str(row.get("filename") or "").removeprefix("../")
    for manifest in (main, vf)
    for row in manifest.get("scrapers", [])
}
removed = []
for path in (ROOT / "providers").glob("*--repatched--*.js"):
    relative = path.relative_to(ROOT).as_posix()
    if relative not in referenced:
        path.unlink()
        removed.append(relative)
print("removed residual bundles:", ", ".join(sorted(removed)) or "none")
