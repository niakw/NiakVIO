#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


# Teach the central published-provider reapply transaction to migrate the
# adaptive-domain wrapper from the configuration embedded in its owned block.
path = ROOT / "scripts" / "reapply_published_overrides.py"
text = path.read_text(encoding="utf-8")
if "ADAPTIVE_DOMAIN_SCRIPT" not in text:
    text = text.replace("import argparse\n", "import argparse\nimport base64\n", 1)

    anchor = 'ADAPTIVE_SCRIPT = ROOT / "scripts" / "provider_patches" / "adaptive_runtime_recovery_v4.py"\n'
    extra = anchor + (
        'ADAPTIVE_DOMAIN_BEGIN = "/* NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1:BEGIN */"\n'
        'ADAPTIVE_DOMAIN_END = "/* NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1:END */"\n'
        'ADAPTIVE_DOMAIN_SCRIPT = ROOT / "scripts" / "provider_patches" / "adaptive_domain_recovery.py"\n'
    )
    if anchor not in text:
        raise SystemExit("reapply: adaptive runtime constant anchor missing")
    text = text.replace(anchor, extra, 1)

    fn_anchor = "\ndef load_manifest(path: Path) -> dict[str, Any] | None:\n"
    fn = '''

def reapply_adaptive_domain_revision(data: bytes) -> tuple[bytes, list[dict[str, Any]]]:
    """Refresh an owned adaptive-domain wrapper from its embedded peer groups."""
    text = data.decode("utf-8", errors="strict")
    start = text.find(ADAPTIVE_DOMAIN_BEGIN)
    if start < 0:
        return data, []
    end = text.find(ADAPTIVE_DOMAIN_END, start)
    if end < 0:
        raise ValueError("unterminated adaptive domain recovery wrapper")
    segment = text[start : end + len(ADAPTIVE_DOMAIN_END)]
    groups = None
    for encoded in re.findall(r'"([A-Za-z0-9+/=]{16,})"', segment):
        try:
            decoded = json.loads(base64.b64decode(encoded).decode("utf-8"))
        except Exception:
            continue
        candidate = (
            decoded
            if isinstance(decoded, list)
            else decoded.get("groups")
            if isinstance(decoded, dict)
            else None
        )
        if isinstance(candidate, list) and all(isinstance(row, dict) for row in candidate):
            groups = candidate
    if not groups:
        return data, []
    spec = importlib.util.spec_from_file_location(
        "nuvio_reapply_adaptive_domain", ADAPTIVE_DOMAIN_SCRIPT
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load adaptive domain patcher: {ADAPTIVE_DOMAIN_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    patched = module.apply(text, options={"groups": groups}).encode("utf-8")
    if patched == data:
        return data, []
    return patched, [{
        "type": "migration",
        "name": "adaptive_domain_implementation_revision",
        "phase": "runtime",
        "profile": "adaptive_domain_recovery",
        "runtime_revision": str(getattr(module, "IMPLEMENTATION_REVISION", "current")),
    }]
'''
    if fn_anchor not in text:
        raise SystemExit("reapply: load_manifest anchor missing")
    text = text.replace(fn_anchor, fn + fn_anchor, 1)

    # Canonical transaction order matters. Migrate the adaptive-domain wrapper
    # first, then let apply_overrides() rebuild its runtime-domain bootstrap at
    # the front exactly once. Doing this in the opposite order makes pass one
    # produce [adaptive-domain][runtime-domain] and pass two reorder it to
    # [runtime-domain][adaptive-domain], changing hashes and versions twice.
    call_anchor = '''        original = path.read_bytes()
        migrated, adaptive_language_repairs = strip_unproven_adaptive_language(original)
        patched, records = apply_overrides(provider_id, migrated, phase="discovery")
        provider_provenance = provenance_rows.get(provider_id) if provenance_rows else None
'''
    call = '''        original = path.read_bytes()
        migrated, adaptive_language_repairs = strip_unproven_adaptive_language(original)
        migrated, domain_revision_records = reapply_adaptive_domain_revision(migrated)
        patched, records = apply_overrides(provider_id, migrated, phase="discovery")
        if domain_revision_records:
            records = list(records) + domain_revision_records
        provider_provenance = provenance_rows.get(provider_id) if provenance_rows else None
'''
    if call_anchor not in text:
        raise SystemExit("reapply: provider transaction anchor missing")
    text = text.replace(call_anchor, call, 1)

    text = text.replace(
        '"runtime_revision": "bounded-binary-v1",',
        '"runtime_revision": "generic-core-v2",',
        1,
    )
    path.write_text(text, encoding="utf-8")

# A domain-prefix regression test must follow the current configured terminal,
# not hard-code a route that the resolver is explicitly allowed to migrate.
path = ROOT / "tests" / "overrides_test.py"
text = path.read_text(encoding="utf-8")
old = '''    source = b'const BASE="https://flemmix.me/";'
    first, records = apply_overrides("flemmix", source)
    assert b"https://flemmix.men/" in first
    assert b"flemmix.menn" not in first
'''
new = '''    source = b'const BASE="https://flemmix.me/";'
    config = json.loads((ROOT / "provider-overrides.json").read_text())
    patch = config["provider_patches"]["flemmix"]
    target_host = (
        (patch.get("runtime_domain_replacements") or patch.get("replacements") or {})
        .get("flemmix.me")
    )
    assert target_host, patch
    first, records = apply_overrides("flemmix", source)
    assert ("https://" + target_host + "/").encode() in first
    assert b"flemmix.menn" not in first
'''
if old in text:
    text = text.replace(old, new, 1)
elif 'assert b"https://flemmix.men/" in first' in text:
    raise SystemExit("overrides_test: unexpected Flemmix prefix fixture shape")
path.write_text(text, encoding="utf-8")

# Keep the published-wrapper migration permanently in the normal regression suite.
path = ROOT / "package.json"
data = json.loads(path.read_text(encoding="utf-8"))
script = data["scripts"]["test"]
anchor = "python3 tests/adaptive_domain_recovery_test.py"
addition = anchor + " && python3 tests/reapply_adaptive_domain_revision_test.py"
if "reapply_adaptive_domain_revision_test.py" not in script:
    if anchor not in script:
        raise SystemExit("package.json: adaptive domain test anchor missing")
    data["scripts"]["test"] = script.replace(anchor, addition, 1)
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("adaptive domain revision migration helper applied")
