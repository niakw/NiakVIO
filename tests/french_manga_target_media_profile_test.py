#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];d=json.loads((ROOT/'provider-overrides.json').read_text());c=d['provider_patches']['french-manga'];s=c['patch_scripts'];assert 'scripts/provider_patches/nuvio_tv_direct_media_v2.py' not in s;assert s.index('scripts/provider_patches/french_manga_player_capture_v1.py')<s.index('scripts/provider_patches/nuvio_tv_target_media_v4.py')<s.index('scripts/provider_patches/stream_output_sanitizer_v5.py');print('French-Manga capture/target profile test passed')
