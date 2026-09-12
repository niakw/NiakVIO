#!/usr/bin/env python3
"""Wire selected current-site provider Legos into provider-overrides.json."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "provider-overrides.json"
PATCHES = {
    "papadustream": "scripts/provider_patches/papadustream_site_runtime_v1.py",
    "animesama-co": "scripts/provider_patches/animesamaco_site_runtime_v1.py",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("providers", nargs="*", choices=sorted(PATCHES))
    args = parser.parse_args()
    selected = args.providers or list(PATCHES)

    data = json.loads(TARGET.read_text(encoding="utf-8"))
    providers = data.get("provider_patches")
    if not isinstance(providers, dict):
        raise AssertionError("provider_patches missing")
    changed = []
    for provider in selected:
        script = PATCHES[provider]
        row = providers.get(provider)
        if not isinstance(row, dict):
            raise AssertionError(f"missing provider override: {provider}")
        scripts = row.get("provider_lego_scripts")
        if scripts is None:
            scripts = []
        if not isinstance(scripts, list):
            raise AssertionError(f"provider_lego_scripts is not a list: {provider}")
        scripts = [str(x) for x in scripts if str(x).strip()]
        if script not in scripts:
            scripts.append(script)
            changed.append(provider)
        row["provider_lego_scripts"] = scripts
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("SITE_RUNTIME_WIRED selected=" + ",".join(selected) + " changed=" + ",".join(changed or ["none"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
