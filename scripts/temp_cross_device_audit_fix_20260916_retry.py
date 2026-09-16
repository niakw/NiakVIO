#!/usr/bin/env python3
from __future__ import annotations
import runpy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ns=runpy.run_path(str(ROOT/'scripts/temp_cross_device_audit_fix_20260916.py'), run_name='cross_device_base')
ns['main']()

# VF audio + VOSTFR subtitles is not multi-audio. Keep subtitle evidence separate.
p=ROOT/'tests/global_stream_presentation_test.py'
t=p.read_text(encoding='utf-8')
t=t.replace('assert row["language"] == "MULTI (VF/VO)", row','assert row["language"] == "VF", row')
t=t.replace('assert {"4k-ultra-hd", "webdl", "hevc", "multi"}.issubset(set(row["badgeIds"])), row','assert {"4k-ultra-hd", "webdl", "hevc", "vf", "vostfr"}.issubset(set(row["badgeIds"])), row\nassert "multi" not in set(row["badgeIds"]), row')
t=t.replace('assert lines[2] == "🇫🇷 MULTI (VF/VO)", lines','assert lines[2] == "🇫🇷 VF", lines')
t=t.replace('assert "🇫🇷 MULTI (VF/VO)" in roundtrip["description"], roundtrip','assert "🇫🇷 VF" in roundtrip["description"], roundtrip')
t=t.replace('assert "🇫🇷 MULTI (VF/VO)" in tv_row["description"]','assert "🇫🇷 VF" in tv_row["description"]')
p.write_text(t,encoding='utf-8')

# Sanitizer owns media validation, final branding owns client-visible title/name.
# Branding therefore must remain OUTSIDE (after) sanitizer, never be treated as
# a predecessor that forces sanitizer relocation behind it.
p=ROOT/'scripts/provider_patches/stream_output_sanitizer_v6.py'
t=p.read_text(encoding='utf-8')
old='''CORE_PREDECESSOR_MARKERS = TARGET_MEDIA_MARKERS + (\n    "/* NUVIO_GLOBAL_STREAM_PRESENTATION_V1:",\n    "/* NUVIO_GLOBAL_PROVIDER_BRANDING_V1:",\n)'''
new='''CORE_PREDECESSOR_MARKERS = TARGET_MEDIA_MARKERS + (\n    "/* NUVIO_GLOBAL_STREAM_PRESENTATION_V1:",\n)'''
if old in t:
    t=t.replace(old,new,1)
elif new not in t:
    raise AssertionError('sanitizer predecessor marker shape drifted')
t=t.replace(
    'A second subtlety matters on durable/LKG rematerialization. Some target-media\nprofiles deliberately remove their old wrapper and append a fresh one.',
    'A second subtlety matters on durable/LKG rematerialization. Some target-media\nprofiles deliberately remove their old wrapper and append a fresh one. Final\nprovider branding is intentionally outside this boundary: sanitizer validates\nmedia first, then branding projects the final verified quality exactly once.'
)
p.write_text(t,encoding='utf-8')

p=ROOT/'tests/stream_output_sanitizer_fail_closed_test.py'
t=p.read_text(encoding='utf-8')
t=t.replace(
    '# Core stream presentation/branding can also be rematerialized after an old\n    # sanitizer. The strict terminal layer must move after them as well.',
    '# Stream presentation is inside the sanitizer, while final provider branding\n    # is outside it. Reapplying V6 must preserve branding after the sanitizer.'
)
t=t.replace(
    'assert branding_pos >= 0 and sanitizer_pos > branding_pos, (branding_pos, sanitizer_pos)',
    'assert branding_pos >= 0 and branding_pos > sanitizer_pos, (branding_pos, sanitizer_pos)'
)
p.write_text(t,encoding='utf-8')

print('retry: audio/subtitle roles separated; sanitizer before final branding')
