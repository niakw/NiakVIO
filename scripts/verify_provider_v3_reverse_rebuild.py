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
    rows = manifest.get("scrapers") or []
    if expected.get("providerCount") != 96 or len(rows) != 96:
        raise SystemExit("Provider v3 reverse rebuild requires exactly 96 providers")
    ids = [str(row.get("id") or "").strip().lower() for row in rows]
    if any(not pid for pid in ids) or len(set(ids)) != 96:
        raise SystemExit("Provider v3 reverse rebuild requires 96 unique non-empty provider ids")
    active = [pid for pid, row in zip(ids, rows) if row.get("enabled") is not False]
    disabled = [pid for pid, row in zip(ids, rows) if row.get("enabled") is False]
    if not active:
        raise SystemExit("Provider v3 reverse rebuild requires at least one enabled provider")
    pur = next((r for r in rows if str(r.get("id","")).lower()=="purstream"), None)
    if not pur or pur.get("canonicalSupportedTypes") != ["movie", "tv"]:
        raise SystemExit("PURSTREAM canonical capability must remain movie/tv only")
    if pur.get("supportedTypes") != ["movie", "tv", "series"]:
        raise SystemExit("PURSTREAM transport compatibility must expose movie/tv/series")
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
        if rebuilt.get("providerCount") != 96 or len(rebuilt.get("providers") or []) != 96:
            raise SystemExit("reverse rebuild did not reconstruct the full 96-provider catalogue")
        if rebuilt.get("generation") != expected.get("generation"):
            raise SystemExit(f"generation mismatch expected={expected.get('generation')} actual={rebuilt.get('generation')}")
        actual_by_id = {str(r["provider"]).lower(): r for r in rebuilt["providers"]}
        if set(actual_by_id) != set(ids):
            raise SystemExit("reverse rebuild provider ids differ from canonical manifest")
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
    print(
        f"PROVIDER_V3_REVERSE_REBUILD_OK providers=96 active={len(active)} disabled={len(disabled)} "
        f"generation={expected['generation'][:16]} byte_identical=96/96 activation_policy=preserved"
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
