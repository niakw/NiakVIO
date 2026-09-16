#!/usr/bin/env python3
from __future__ import annotations
import runpy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT/'scripts/temp_cross_device_audit_fix_20260916.py'), run_name='__main__')

p=ROOT/'tests/global_stream_presentation_test.py'
t=p.read_text(encoding='utf-8')
t=t.replace('assert row["language"] == "MULTI (VF/VO)", row','assert row["language"] == "VF", row')
t=t.replace('assert {"4k-ultra-hd", "webdl", "hevc", "multi"}.issubset(set(row["badgeIds"])), row','assert {"4k-ultra-hd", "webdl", "hevc", "vf", "vostfr"}.issubset(set(row["badgeIds"])), row\nassert "multi" not in set(row["badgeIds"]), row')
t=t.replace('assert lines[2] == "🇫🇷 MULTI (VF/VO)", lines','assert lines[2] == "🇫🇷 VF", lines')
t=t.replace('assert "🇫🇷 MULTI (VF/VO)" in roundtrip["description"], roundtrip','assert "🇫🇷 VF" in roundtrip["description"], roundtrip')
t=t.replace('assert "🇫🇷 MULTI (VF/VO)" in tv_row["description"]','assert "🇫🇷 VF" in tv_row["description"]')
p.write_text(t,encoding='utf-8')
print('retry: subtitles no longer promoted to multi-audio')
