#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_catalogue_identity_media.py"


def load_module():
    spec = importlib.util.spec_from_file_location("catalogue_audit_coverage", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_module()
    # Upstream/network failures are per-stream availability signals, not proof
    # that the provider emitted a structurally invalid HLS graph.
    for error in (
        "hls_variant_http_500",
        "hls_variant_http_502",
        "hls_audio_timeout",
        "hls_variant_fetch failed",
    ):
        assert module.is_transient_media_error(error), error
    for error in (
        "hls_variant_http_404",
        "hls_variant_invalid_manifest",
        "hls_audio_invalid_manifest",
    ):
        assert not module.is_transient_media_error(error), error
    tasks, _vf_ids = module.build_tasks()
    by_provider: dict[str, set[str]] = {}
    for task in tasks:
        by_provider.setdefault(task["identity"]["provider_id"], set()).add(task["fixture_name"])

    manifest = module.load_json(module.MANIFEST)
    for row in manifest.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        provider_id = str(row.get("id") or "").strip().casefold()
        if not provider_id or not (ROOT / str(row.get("filename") or "")).is_file():
            continue
        types = module.canonical_types(row)
        fixtures = by_provider.get(provider_id, set())
        if "movie" in types:
            assert "strict_movie_identity" in fixtures, (provider_id, fixtures)
            assert "impossible_movie" in fixtures, (provider_id, fixtures)
        if "tv" in types:
            assert "kdrama_squid_game_s01e01" in fixtures, (provider_id, fixtures)
        if "anime" in types:
            assert "vf_jjk_s01e01" in fixtures, (provider_id, fixtures)

    print(f"catalogue/media audit coverage test passed ({len(by_provider)} providers)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
