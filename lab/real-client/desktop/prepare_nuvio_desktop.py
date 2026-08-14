#!/usr/bin/env python3
from pathlib import Path
import json
import shutil
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: prepare_nuvio_desktop.py <nuvio-desktop-dir> <niakvio-dir>")

desktop = Path(sys.argv[1]).resolve()
niakvio = Path(sys.argv[2]).resolve()
workspace = niakvio.parent
runtime = workspace / "desktop-real-client-runtime"
runtime.mkdir(parents=True, exist_ok=True)

manifest = json.loads((niakvio / "manifest.json").read_text(encoding="utf-8"))
rows = {
    str(row.get("id") or "").casefold(): row
    for row in manifest.get("scrapers", [])
    if isinstance(row, dict)
}
selection = []
for provider_id in ("moviebox", "netmirror", "streamzo"):
    row = rows.get(provider_id)
    if not isinstance(row, dict):
        raise SystemExit(f"missing provider in tested manifest: {provider_id}")
    filename = str(row.get("filename") or "")
    source = niakvio / filename
    if not filename.startswith("providers/") or not source.is_file():
        raise SystemExit(f"invalid published provider filename for {provider_id}: {filename}")
    local_name = f"{provider_id}.js"
    shutil.copy2(source, runtime / local_name)
    enabled = row.get("enabled") is True
    version = str(row.get("version") or "")
    selection.append(f"{provider_id}\t{str(enabled).lower()}\t{version}\t{filename}\t{local_name}")
    print(
        f"FIELD_DESKTOP_SELECTION provider={provider_id} enabled={enabled} "
        f"version={version} filename={filename}"
    )
(runtime / "selection.tsv").write_text("\n".join(selection) + "\n", encoding="utf-8")

test_dest = desktop / "composeApp/src/desktopTest/kotlin/com/nuvio/app/features/plugins"
test_dest.mkdir(parents=True, exist_ok=True)
shutil.copy2(
    niakvio / "lab/real-client/desktop/NiakvioRealProviderDesktopTest.kt",
    test_dest / "NiakvioRealProviderDesktopTest.kt",
)
print("NuvioDesktop real-client test prepared from tested manifest")
