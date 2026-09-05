#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "provider_release_versioning.py"
spec = importlib.util.spec_from_file_location("provider_release_versioning", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fixture() -> dict:
    return {
        "name": "NiakVIO",
        "version": "5.21.31",
        "scrapers": [
            {
                "id": f"P{index:02d}",
                "version": "1.2.3",
                "filename": f"providers/p{index:02d}.js",
            }
            for index in range(96)
        ],
    }


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        baseline = fixture()
        current = json.loads(json.dumps(baseline))
        current["scrapers"][7]["filename"] = "providers/p07-new.js"
        write(root / "before.json", baseline)
        write(root / "manifest.json", current)
        write(root / "package.json", {"version": "5.21.31"})
        write(root / "package-lock.json", {"version": "5.21.31", "packages": {"": {"version": "5.21.31"}}})
        write(root / "provider_catalog.json", {"manifestMeta": {"general": {"version": "5.21.31"}, "vf": {"version": "5.21.31"}}})
        write(root / "sources.json", {"repository": {"manifest_version": "5.21.31"}, "manifest_version": "5.21.31"})

        result = module.apply_bump(
            root / "manifest.json",
            root / "before.json",
            force_all=False,
            target_release=None,
        )
        assert result["release"] == "5.21.32"
        assert result["providers"] == ["p07"]
        manifest = module.load(root / "manifest.json")
        rows = {row["id"].casefold(): row for row in manifest["scrapers"]}
        assert rows["p07"]["version"] == "1.2.4"
        assert rows["p08"]["version"] == "1.2.3"
        assert module.load(root / "package.json")["version"] == "5.21.32"
        assert module.load(root / "package-lock.json")["packages"][""]["version"] == "5.21.32"
        assert module.load(root / "provider_catalog.json")["manifestMeta"]["vf"]["version"] == "5.21.32"
        assert module.load(root / "sources.json")["repository"]["manifest_version"] == "5.21.32"

        all_before = fixture()
        all_current = json.loads(json.dumps(all_before))
        write(root / "before-all.json", all_before)
        write(root / "manifest-all.json", all_current)
        result = module.apply_bump(
            root / "manifest-all.json",
            root / "before-all.json",
            force_all=True,
            target_release="5.21.32",
        )
        assert len(result["providers"]) == 96
        assert all(row["version"] == "1.2.4" for row in module.load(root / "manifest-all.json")["scrapers"])

    print("provider release versioning tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
