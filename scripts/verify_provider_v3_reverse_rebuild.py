#!/usr/bin/env python3
"""Rebuild the current active Global+France Provider-v3 generation and prove deterministic bytes.

The workspace materializer owns ProviderBase + DATA + Lego composition. Published
Provider JS additionally goes through the conservative NiakVIO minimizer, so this
proof validates the active-provider workspace generation and verifies that applying
that minimizer is deterministic before publication. Historical provider-old
snapshots are intentionally outside current reconstruction authority.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from current_provider_scope import projection_active_provider_count, projection_active_provider_ids

from materialize_provider_v3_all import materialize_all
from provider_v3_minimizer import minimize_provider_text
from provider_materialization_generation import materialization_generation

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ROOT / "provider-v3-materialization.json"
MANIFEST = ROOT / "manifest.json"
CATALOG = ROOT / "provider_catalog.json"
EXPECTED_PROVIDER_COUNT = projection_active_provider_count()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def final_publication_bytes(raw: bytes) -> bytes:
    """Apply the exact publication minimizer and prove its fixed point."""
    minimized = minimize_provider_text(raw.decode("utf-8", errors="strict")).encode("utf-8")
    second = minimize_provider_text(minimized.decode("utf-8", errors="strict")).encode("utf-8")
    if second != minimized:
        raise ValueError("NiakVIO minimizer is not a fixed point")
    return minimized


def main() -> int:
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    active_ids = projection_active_provider_ids()
    ids = sorted(active_ids)

    if expected.get("providerCount") != EXPECTED_PROVIDER_COUNT:
        raise SystemExit(
            f"Provider v3 reverse rebuild requires exactly {EXPECTED_PROVIDER_COUNT} current providers"
        )
    expected_ids = {
        str(row.get("provider") or "").strip().casefold().replace("_", "-")
        for row in expected.get("providers") or []
        if isinstance(row, dict)
    }
    if expected_ids != active_ids or len(expected_ids) != EXPECTED_PROVIDER_COUNT:
        raise SystemExit(
            "Provider v3 reverse rebuild materialization authority differs from "
            "the active Global+France projection union"
        )

    archived_slugs = {
        path.name.split("--", 1)[0].casefold()
        for path in (ROOT / "provider-old").glob("*.js")
        if path.is_file()
    }
    # Historical snapshots may legitimately share an identity with a current
    # provider after reactivation.  Publication authority is path/byte based,
    # not identity-name exclusive: every active identity must resolve to the
    # current providers/ tree, while provider-old/ remains provenance only.
    current_rows: dict[str, dict] = {
        str(row.get("id") or "").strip().casefold().replace("_", "-"): row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict)
    }
    for record in catalog.get("providers") or []:
        if not isinstance(record, dict):
            continue
        scraper = record.get("scraper")
        if not isinstance(scraper, dict):
            continue
        provider_id = str(
            record.get("canonicalId") or scraper.get("id") or ""
        ).strip().casefold().replace("_", "-")
        if provider_id and provider_id not in current_rows:
            current_rows[provider_id] = scraper
    for provider_id in ids:
        row = current_rows.get(provider_id)
        if not isinstance(row, dict):
            raise SystemExit(f"{provider_id}: active projection row missing")
        filename = str(row.get("filename") or "").replace("\\", "/")
        while filename.startswith("../"):
            filename = filename[3:]
        if not filename.startswith("providers/"):
            raise SystemExit(
                f"{provider_id}: active projection must execute providers/ bytes, got {filename!r}"
            )

    with tempfile.TemporaryDirectory(prefix="niakvio-v3-rebuild-") as tmp_raw:
        tmp = Path(tmp_raw)
        tmp_manifest = tmp / "manifest.json"
        tmp_catalog = tmp / "provider_catalog.json"
        tmp_manifest.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        tmp_catalog.write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        rebuilt = materialize_all(
            source_manifest_path=tmp_manifest,
            source_catalog_path=tmp_catalog,
            overrides_path=ROOT / "provider-overrides.json",
            output_dir=tmp / "providers",
            report_path=tmp / "report.json",
        )
        rebuilt_rows = rebuilt.get("providers") or []
        if rebuilt.get("providerCount") != EXPECTED_PROVIDER_COUNT or len(rebuilt_rows) != EXPECTED_PROVIDER_COUNT:
            raise SystemExit("reverse rebuild did not reconstruct the full active provider catalogue")
        actual_by_id = {str(row["provider"]).casefold(): row for row in rebuilt_rows}
        published_rows: list[dict[str, str]] = []
        expected_by_id = {
            str(row["provider"]).casefold(): row
            for row in (expected.get("providers") or [])
            if isinstance(row, dict)
        }
        if set(actual_by_id) != active_ids or set(expected_by_id) != active_ids:
            raise SystemExit("reverse rebuild provider ids differ from current Global+France authority")

        for provider_id in ids:
            actual = actual_by_id[provider_id]
            expected_row = expected_by_id[provider_id]
            rebuilt_file = tmp / "providers" / Path(str(actual["file"])).name
            if not rebuilt_file.is_file():
                raise SystemExit(f"{provider_id}: rebuilt workspace artifact missing")
            raw = rebuilt_file.read_bytes()
            raw_digest = sha256_bytes(raw)
            if raw_digest != str(actual.get("sha256") or ""):
                raise SystemExit(f"{provider_id}: rebuilt workspace report digest mismatch")
            if str(actual.get("providerDataSha256") or "") != str(expected_row.get("providerDataSha256") or ""):
                raise SystemExit(f"{provider_id}: structured Provider DATA digest mismatch")

            try:
                published = final_publication_bytes(raw)
            except ValueError as exc:
                raise SystemExit(f"{provider_id}: {exc}") from exc
            published_digest = sha256_bytes(published)
            if published_digest != str(expected_row.get("sha256") or ""):
                raise SystemExit(f"{provider_id}: final published byte digest mismatch")
            expected_file = Path(str(expected_row.get("file") or "")).name
            if expected_file and published_digest[:16] not in expected_file:
                raise SystemExit(f"{provider_id}: content-addressed published filename mismatch")
            published_rows.append({"provider": provider_id, "sha256": published_digest})

    published_generation = materialization_generation(published_rows)
    if published_generation != expected.get("generation"):
        raise SystemExit(
            f"published generation mismatch expected={expected.get('generation')} "
            f"actual={published_generation}"
        )

    print(
        "PROVIDER_V3_REVERSE_REBUILD_OK "
        f"providers={EXPECTED_PROVIDER_COUNT} historical={len(archived_slugs)} "
        f"generation={str(expected['generation'])[:16]} "
        f"workspace_byte_identical={EXPECTED_PROVIDER_COUNT}/{EXPECTED_PROVIDER_COUNT} "
        f"minimizer_fixed_point={EXPECTED_PROVIDER_COUNT}/{EXPECTED_PROVIDER_COUNT} terser=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
