#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "scripts" / "probe_waf_browser_session.py").read_text(encoding="utf-8")

for required in (
    '"brave-browser"',
    '"brave"',
    'Brave Browser.app/Contents/MacOS/Brave Browser',
    'Google Chrome.app/Contents/MacOS/Google Chrome',
    'Chromium.app/Contents/MacOS/Chromium',
    'Safari is intentionally excluded',
):
    assert required in source, required
