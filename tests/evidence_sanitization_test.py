#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from evidence_sanitization import REDACTED, redact_text, redact_url, sanitize_evidence

JWT = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJ1aWQiOjAsInBpZCI6MjA0NjcsImV4cCI6MTc4NTk0MDMwMn0."
    "ruY86oQXdWGHVj4LrKBK_caPZiLFYbzfooH4ogOf7s"
)

source_url = f"https://lecteurvideo.example/embed.php?id=18230&t={JWT}&lang=fr"
safe_url = redact_url(source_url)
assert "lecteurvideo.example/embed.php" in safe_url
assert "id=18230" in safe_url
assert "lang=fr" in safe_url
assert JWT not in safe_url
assert "%3Credacted%3E" in safe_url

captured = (
    f'fetch("{source_url}"); '
    'api_key="1234567890abcdef"; '
    'Authorization: Bearer abcdefghijklmnopqrstuvwxyz; '
    '<iframe data-secret="embeddedSecret123"></iframe>; '
    '<iframe data-secret=\\"escapedSecret456\\"></iframe>; '
    r'<iframe data-secret=\\\"nestedEscapedSecret789\\\"></iframe>; '
    '<script data-cf-beacon=\'{"token":"beaconToken123"}\'></script>'
)
safe_text = redact_text(captured)
assert JWT not in safe_text
assert "1234567890abcdef" not in safe_text
assert "abcdefghijklmnopqrstuvwxyz" not in safe_text
assert "embeddedSecret123" not in safe_text
assert "escapedSecret456" not in safe_text
assert "nestedEscapedSecret789" not in safe_text
assert "beaconToken123" not in safe_text
assert "<redacted>" in safe_text

payload = {
    "requested_url": source_url,
    "status": 200,
    "headers": {
        "content-type": "text/html",
        "set-cookie": "session=super-secret-session; Path=/; HttpOnly",
        "location": source_url,
    },
    "preview": f'<iframe src="{source_url}"></iframe>',
    "candidate_urls": [
        source_url,
        "https://media.example/master.m3u8?quality=1080p",
    ],
}
safe = sanitize_evidence(payload)
encoded = json.dumps(safe, sort_keys=True)

assert JWT not in encoded
assert "super-secret-session" not in encoded
assert safe["headers"]["set-cookie"] == REDACTED
assert safe["headers"]["content-type"] == "text/html"
assert safe["status"] == 200
assert "quality=1080p" in safe["candidate_urls"][1]
assert "id=18230" in safe["requested_url"]

print("persisted evidence sanitization test passed")
