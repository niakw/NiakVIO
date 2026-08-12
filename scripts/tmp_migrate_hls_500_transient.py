#!/usr/bin/env python3
from pathlib import Path

# One-shot migration; the workflow removes this helper after successful validation.
ROOT = Path(__file__).resolve().parents[1]
audit = ROOT / 'scripts' / 'audit_catalogue_identity_media.py'
test = ROOT / 'tests' / 'catalogue_audit_coverage_test.py'

text = audit.read_text(encoding='utf-8')
old = '        "429", "too many requests", "502", "503", "504",\n'
new = '        "429", "too many requests", "500", "502", "503", "504",\n'
if new not in text:
    if old not in text:
        raise SystemExit('transient media token anchor missing')
    text = text.replace(old, new, 1)
audit.write_text(text, encoding='utf-8')

source = test.read_text(encoding='utf-8')
anchor = '    module = load_module()\n'
block = '''    module = load_module()\n    # Upstream/network failures are per-stream availability signals, not proof\n    # that the provider emitted a structurally invalid HLS graph.\n    for error in (\n        "hls_variant_http_500",\n        "hls_variant_http_502",\n        "hls_audio_timeout",\n        "hls_variant_fetch failed",\n    ):\n        assert module.is_transient_media_error(error), error\n    for error in (\n        "hls_variant_http_404",\n        "hls_variant_invalid_manifest",\n        "hls_audio_invalid_manifest",\n    ):\n        assert not module.is_transient_media_error(error), error\n'''
if block not in source:
    if anchor not in source:
        raise SystemExit('catalogue audit test anchor missing')
    source = source.replace(anchor, block, 1)
test.write_text(source, encoding='utf-8')
print('HLS HTTP 500 transient audit migration applied')
