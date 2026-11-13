#!/usr/bin/env python3
"""Availability needs exact TMDB catalogue/episode metadata for fair provider probes."""
from pathlib import Path

workflow=Path(".github/workflows/availability.yml").read_text(encoding="utf-8")
run=workflow.split("      - name: Run low-cost availability diagnostics\n", 1)[1].split(
    "      - name: Upload diagnostic result\n", 1
)[0]
assert "TMDB_API_KEY: ${{ secrets.TMDB_API_KEY }}" in run
assert "TMDB_ACCESS_TOKEN: ${{ secrets.TMDB_ACCESS_TOKEN }}" in run
assert 'if [ -z "${TMDB_API_KEY:-}" ] && [ -z "${TMDB_ACCESS_TOKEN:-}" ]; then' in run
assert "FIELD_AVAILABILITY_DIAGNOSTIC_BLOCKED reason=missing_tmdb_credential" in run
assert 'node scripts/health_check.mjs --availability' in run
assert "set -euo pipefail" in run
report=workflow.split("  report:\n", 1)[1]
assert "needs: check" in report
assert "Update reports without applying manifest toggles" in report
assert "TMDB_API_KEY" not in report and "TMDB_ACCESS_TOKEN" not in report
assert "manifest_changed" not in run
assert "git push" not in run
assert 'NUVIO_HEALTH_OUTPUT: health-output' in run
print("AVAILABILITY_TMDB_AUTH_CONTRACT_OK diagnostic gated before report publication")
