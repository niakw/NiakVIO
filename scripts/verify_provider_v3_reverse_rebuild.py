#!/usr/bin/env python3
"""Rebuild all 96 Provider v3 artifacts from production DATA/Core Lego and compare raw bytes."""
from __future__ import annotations
import hashlib, json, tempfile
from pathlib import Path
from materialize_provider_v3_all import materialize_all

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ROOT / "provider-v3-materialization.json"
MANIFEST = ROOT / "manifest.json"

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if expected.get("providerCount") != 96 or len(manifest.get("scrapers") or []) != 96:
        raise SystemExit("Provider v3 reverse rebuild requires exactly 96 providers")
    movix = next((r for r in manifest["scrapers"] if str(r.get("id","")).lower()=="movix"), None)
    pur = next((r for r in manifest["scrapers"] if str(r.get("id","")).lower()=="purstream"), None)
    if not movix or movix.get("enabled") is not False:
        raise SystemExit("MOVIX must remain disabled in production")
    if not pur or pur.get("supportedTypes") != ["movie", "tv"]:
        raise SystemExit("PURSTREAM must remain movie/tv only")
    with tempfile.TemporaryDirectory(prefix="niakvio-v3-rebuild-") as tmp_raw:
        tmp = Path(tmp_raw)
        tmp_manifest = tmp / "manifest.json"
        tmp_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        rebuilt = materialize_all(
            source_manifest_path=tmp_manifest,
            overrides_path=ROOT / "provider-overrides.json",
            output_dir=tmp / "providers",
            report_path=tmp / "report.json",
        )
        if rebuilt.get("generation") != expected.get("generation"):
            raise SystemExit(f"generation mismatch expected={expected.get('generation')} actual={rebuilt.get('generation')}")
        actual_by_id = {str(r["provider"]).lower(): r for r in rebuilt["providers"]}
        for row in expected["providers"]:
            pid = str(row["provider"]).lower()
            actual = actual_by_id.get(pid)
            if not actual or actual.get("sha256") != row.get("sha256"):
                raise SystemExit(f"{pid}: reconstructed digest mismatch")
            published = ROOT / row["file"]
            rebuilt_file = tmp / "providers" / Path(actual["file"]).name
            if not published.is_file():
                raise SystemExit(f"{pid}: published artifact missing: {published}")
            if sha256(published) != row["sha256"] or published.read_bytes() != rebuilt_file.read_bytes():
                raise SystemExit(f"{pid}: published bytes differ from reconstruction")
    print(f"PROVIDER_V3_REVERSE_REBUILD_OK providers=96 generation={expected['generation'][:16]} byte_identical=96/96")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
