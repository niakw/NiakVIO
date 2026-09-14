#!/usr/bin/env python3
"""Rebuild the current Hub46 workspace generation and prove deterministic bytes.

The workspace materializer owns ProviderBase + DATA + Lego composition. Published
Provider JS additionally goes through the conservative NiakVIO minimizer, so this
proof validates the 46-provider workspace generation and verifies that applying
that minimizer is deterministic before publication. Historical provider-old
snapshots are intentionally outside current reconstruction authority.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from materialize_provider_v3_all import materialize_all
from provider_v3_minimizer import minimize_provider_text

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ROOT / "provider-v3-materialization.json"
MANIFEST = ROOT / "manifest.json"
EXPECTED_PROVIDER_COUNT = 46
HISTORICAL_PROVIDER_COUNT = 50


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict)]

    if expected.get("providerCount") != EXPECTED_PROVIDER_COUNT or len(rows) != EXPECTED_PROVIDER_COUNT:
        raise SystemExit(
            f"Provider v3 reverse rebuild requires exactly {EXPECTED_PROVIDER_COUNT} current providers"
        )
    ids = [str(row.get("id") or "").strip().casefold() for row in rows]
    if any(not provider_id for provider_id in ids) or len(set(ids)) != EXPECTED_PROVIDER_COUNT:
        raise SystemExit("Provider v3 reverse rebuild requires 46 unique non-empty provider ids")

    archived_slugs = {
        path.name.split("--", 1)[0].casefold()
        for path in (ROOT / "provider-old").glob("*.js")
        if path.is_file()
    }
    if len(archived_slugs) != HISTORICAL_PROVIDER_COUNT:
        raise SystemExit(
            f"historical provider archive drift: expected {HISTORICAL_PROVIDER_COUNT}, got {len(archived_slugs)}"
        )
    if set(ids) & archived_slugs:
        raise SystemExit("current providers leaked into provider-old historical authority")

    with tempfile.TemporaryDirectory(prefix="niakvio-v3-rebuild-") as tmp_raw:
        tmp = Path(tmp_raw)
        tmp_manifest = tmp / "manifest.json"
        tmp_manifest.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        rebuilt = materialize_all(
            source_manifest_path=tmp_manifest,
            overrides_path=ROOT / "provider-overrides.json",
            output_dir=tmp / "providers",
            report_path=tmp / "report.json",
        )
        rebuilt_rows = rebuilt.get("providers") or []
        if rebuilt.get("providerCount") != EXPECTED_PROVIDER_COUNT or len(rebuilt_rows) != EXPECTED_PROVIDER_COUNT:
            raise SystemExit("reverse rebuild did not reconstruct the full Hub46 catalogue")
        if rebuilt.get("generation") != expected.get("generation"):
            raise SystemExit(
                f"generation mismatch expected={expected.get('generation')} actual={rebuilt.get('generation')}"
            )

        actual_by_id = {str(row["provider"]).casefold(): row for row in rebuilt_rows}
        expected_by_id = {
            str(row["provider"]).casefold(): row
            for row in (expected.get("providers") or [])
            if isinstance(row, dict)
        }
        if set(actual_by_id) != set(ids) or set(expected_by_id) != set(ids):
            raise SystemExit("reverse rebuild provider ids differ from current manifest/report")

        for provider_id in ids:
            actual = actual_by_id[provider_id]
            expected_row = expected_by_id[provider_id]
            rebuilt_file = tmp / "providers" / Path(str(actual["file"])).name
            if not rebuilt_file.is_file():
                raise SystemExit(f"{provider_id}: rebuilt workspace artifact missing")
            raw = rebuilt_file.read_bytes()
            raw_digest = sha256_bytes(raw)
            if raw_digest != str(actual.get("sha256") or ""):
                raise SystemExit(f"{provider_id}: rebuilt report digest mismatch")
            if raw_digest != str(expected_row.get("sha256") or ""):
                raise SystemExit(f"{provider_id}: canonical workspace digest mismatch")

            minimized = minimize_provider_text(raw.decode("utf-8", errors="strict")).encode("utf-8")
            second = minimize_provider_text(minimized.decode("utf-8", errors="strict")).encode("utf-8")
            if second != minimized:
                raise SystemExit(f"{provider_id}: NiakVIO minimizer is not a fixed point")

    print(
        "PROVIDER_V3_REVERSE_REBUILD_OK "
        f"providers={EXPECTED_PROVIDER_COUNT} historical={HISTORICAL_PROVIDER_COUNT} "
        f"generation={str(expected['generation'])[:16]} workspace_byte_identical=46/46 "
        "minimizer_fixed_point=46/46 terser=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
