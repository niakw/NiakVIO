#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'scripts' / 'audit_catalogue_identity_media.py'
PACKAGE = ROOT / 'package.json'

source = AUDIT.read_text(encoding='utf-8')

anchor = '''def load_json(path: Path) -> dict[str, Any]:\n    value = json.loads(path.read_text(encoding="utf-8"))\n    if not isinstance(value, dict):\n        raise ValueError(f"invalid JSON object: {path}")\n    return value\n\n\n'''
helper = '''def is_transient_media_error(value: Any) -> bool:\n    """Network/timing failures are inconclusive, not structural media-graph corruption."""\n    text = str(value or "").casefold()\n    transient_tokens = (\n        "timeout", "timed out", "operation was aborted", "aborterror",\n        "econnreset", "econnrefused", "enotfound", "eai_again",\n        "network", "fetch failed", "socket", "temporary failure",\n        "429", "too many requests", "502", "503", "504",\n    )\n    return any(token in text for token in transient_tokens)\n\n\n'''
if 'def is_transient_media_error' not in source:
    if anchor not in source:
        raise SystemExit('load_json anchor missing')
    source = source.replace(anchor, anchor + helper, 1)

source = source.replace(
'''    hls_variant_failures = 0\n    hls_audio_failures = 0\n''',
'''    hls_variant_failures = 0\n    hls_audio_failures = 0\n    hls_transient_failures = 0\n''', 1)

old = '''            if str(error).startswith("hls_variant_"):\n                hls_variant_failures += 1\n            if str(error).startswith("hls_audio_"):\n                hls_audio_failures += 1\n'''
new = '''            hls_error = str(error).startswith("hls_variant_") or str(error).startswith("hls_audio_")\n            transient = hls_error and is_transient_media_error(error)\n            if transient:\n                hls_transient_failures += 1\n            elif str(error).startswith("hls_variant_"):\n                hls_variant_failures += 1\n            elif str(error).startswith("hls_audio_"):\n                hls_audio_failures += 1\n'''
if old in source:
    source = source.replace(old, new, 1)
elif 'hls_transient_failures += 1' not in source:
    raise SystemExit('HLS failure block missing')

source = source.replace(
'''        "hls_audio_failures": hls_audio_failures,\n''',
'''        "hls_audio_failures": hls_audio_failures,\n        "hls_transient_failures": hls_transient_failures,\n''', 1)
source = source.replace(
'''            "hls_child_or_external_audio_failure": "broken_media_graph",\n''',
'''            "hls_structural_child_or_external_audio_failure": "broken_media_graph",\n            "hls_timeout_or_network_failure": "inconclusive_media_probe_not_publish_blocker",\n''', 1)
source = source.replace('"schema_version": 2,', '"schema_version": 3,', 1)
AUDIT.write_text(source, encoding='utf-8')

TEST = ROOT / 'tests' / 'catalogue_audit_transient_hls_test.py'
TEST.write_text('''#!/usr/bin/env python3\nfrom __future__ import annotations\n\nimport importlib.util\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\npath = ROOT / "scripts" / "audit_catalogue_identity_media.py"\nspec = importlib.util.spec_from_file_location("catalogue_audit", path)\nmodule = importlib.util.module_from_spec(spec)\nassert spec.loader is not None\nspec.loader.exec_module(module)\n\nassert module.is_transient_media_error("hls_variant_TimeoutError: The operation was aborted due to timeout")\nassert module.is_transient_media_error("hls_audio_fetch failed")\nassert module.is_transient_media_error("hls_variant_HTTP 503")\nassert not module.is_transient_media_error("hls_variant_invalid_playlist")\nassert not module.is_transient_media_error("hls_audio_declared_track_missing")\n\nprobe = {"streams": [\n    {"media": {"kind": "hls", "hls_master": True, "error": "hls_variant_TimeoutError: The operation was aborted due to timeout"}},\n    {"media": {"kind": "hls", "hls_master": True, "error": "hls_variant_invalid_playlist"}},\n]}\nsummary = module.summarize_media(probe)\nassert summary["hls_transient_failures"] == 1, summary\nassert summary["hls_variant_failures"] == 1, summary\nassert summary["hls_audio_failures"] == 0, summary\nprint("catalogue audit transient-vs-structural HLS tests passed")\n''', encoding='utf-8')

pkg = PACKAGE.read_text(encoding='utf-8')
needle = ' && python3 tests/global_catalogue_alias_recovery_test.py'
addition = needle + ' && python3 tests/catalogue_audit_transient_hls_test.py'
if 'tests/catalogue_audit_transient_hls_test.py' not in pkg:
    if needle not in pkg:
        raise SystemExit('package test anchor missing')
    pkg = pkg.replace(needle, addition, 1)
PACKAGE.write_text(pkg, encoding='utf-8')

print('transient HLS audit classification migrated')
