#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, "scripts/upgrade_domain_refresh_publication_v3.py"], cwd=ROOT, check=True)

scripts = str(ROOT / "scripts")
if scripts not in sys.path:
    sys.path.insert(0, scripts)

path = ROOT / "scripts" / "domain_refresh_transaction_v2.py"
spec = importlib.util.spec_from_file_location("domain_refresh_transaction_v3_contract", path)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# A domain-only CONFIG rotation must preserve the accepted generation's filename
# stage. Source-qualified publications retain their source namespace.
digest = "ab" * 32
assert module.source_qualified_provider_name(
    "demo", Path("providers/demo--nuvio--0011223344556677.js"), digest
) == "demo--nuvio--abababababababab.js"
assert module.source_qualified_provider_name(
    "demo", Path("providers/demo--nuvio-tv-global--0011223344556677.js"), digest
) == "demo--nuvio-tv-global--abababababababab.js"

# Current Hub46 publication uses the unqualified workspace/content-addressed
# grammar. Rotating only some CONFIG blocks must keep those providers in that
# grammar instead of creating a mixed 34/12 manifest stage.
assert module.source_qualified_provider_name(
    "demo", Path("providers/demo-0011223344556677.js"), digest
) == "demo-abababababababab.js"

# Audit-quarantine is a transient publication suffix, not a permanent source.
assert module.source_qualified_provider_name(
    "demo", Path("providers/demo--nuvio-audit-quarantine--0011223344556677.js"), digest
) == "demo--nuvio--abababababababab.js"

# Generic A -> B domain rotation must update only chains connected to A while
# leaving unrelated execution/API substitutions untouched.
patch = {
    "official_site": "https://a.example",
    "official_hub": "https://hub-old.example",
    "runtime_domain_replacements": {
        "legacy.example": "a.example",
        "api-old.example": "api-new.example",
        "b.example": "a.example",
    },
    "domain_substitutions": {"older.example": "a.example"},
    "replacements": {"textual-old.example": "a.example"},
}
changed = module.sync_patch_domain_authority(patch, {"hub": "https://hub.example/"}, "https://b.example")
assert patch["official_site"] == "https://b.example"
assert patch["official_hub"] == "https://hub.example"
assert patch["runtime_domain_replacements"]["legacy.example"] == "b.example"
assert patch["runtime_domain_replacements"]["a.example"] == "b.example"
assert "b.example" not in patch["runtime_domain_replacements"]
assert patch["runtime_domain_replacements"]["api-old.example"] == "api-new.example"
assert patch["domain_substitutions"]["older.example"] == "b.example"
assert patch["replacements"]["textual-old.example"] == "b.example"
assert {"official_site", "official_hub", "runtime_domain_replacements", "domain_substitutions", "replacements"}.issubset(set(changed))

source = path.read_text(encoding="utf-8")
assert 'new_rel = f"providers/{source_qualified_provider_name(provider_id, old_path, digest)}"' in source
assert 'source = parts[-2] if len(parts) >= 3 else "nuvio"' not in source
assert 'return f"{_safe_fragment(provider_id.casefold())}-{digest[:16]}.js"' in source
assert "allmat.provider_model(provider_id, patch, capability, static_row)" in source
assert "replace_provider_fix(" in source
assert "domain refresh changed bytes outside CONFIG Lego" in source
print("domain refresh publication v3 contract passed: full CONFIG + filename-stage preservation + generic A->B derivatives")
