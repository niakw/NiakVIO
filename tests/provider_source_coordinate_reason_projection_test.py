#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
reasons = {
    "provider_source_coordinate",
    "provider_source_coordinate_mismatch",
    "provider_source_title_mismatch",
    "provider_source_identity_incomplete",
}
for relative in (
    "scripts/export_retest_brain_evidence.py",
    "scripts/merge_retest_brain_evidence_history.py",
    "scripts/check_cross_provider_playback.py",
):
    text = (ROOT / relative).read_text(encoding="utf-8")
    missing = sorted(reason for reason in reasons if reason not in text)
    assert not missing, (relative, missing)
print("provider source-coordinate evidence reasons retained across public projections")
