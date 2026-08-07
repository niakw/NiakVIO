#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from apply_provider_overrides import apply_overrides


# French-Manga intentionally replaces an older generic stream wrapper with the
# stricter NuvioTV direct-media resolver. On a published artifact, a later deep
# pass can therefore add an intermediate wrapper and remove it again. The final
# bytes are unchanged, so the override transaction must not report an effective
# patch record for that pass.
source = b'''async function getStreams(){return [{url:"https://example.invalid/embed/1"}]};module.exports={getStreams};'''
first, first_records = apply_overrides("french-manga", source)
assert first != source
assert b"NUVIO_TV_DIRECT_MEDIA_V2" in first
assert any(
    isinstance(row, dict)
    and row.get("type") == "patch_script"
    and row.get("path") == "scripts/provider_patches/nuvio_tv_direct_media_v2.py"
    for row in first_records
), first_records

second, second_records = apply_overrides("french-manga", first)
assert second == first
assert second_records == [], second_records

print("override net-noop regression test passed")
