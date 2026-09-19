#!/usr/bin/env python3
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts" / "normalize_stream_presentation_v12.py"
spec = importlib.util.spec_from_file_location("presentation_normalizer", path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

sample = 'REVISION = "all-providers-client-projection-evidence-language-v25"\n'
assert module.active_revision(sample) == "all-providers-client-projection-evidence-language-v25"
assert module.revision_number(module.active_revision(sample)) == 25
assert module.active_revision('REVISION = "all-providers-client-projection-language-roles-v23"') is not None
assert module.active_revision('REVISION = "all-providers-client-projection-v21"') is None

current = (ROOT / "scripts" / "provider_patches" / "global_stream_presentation_v1.py").read_text(encoding="utf-8")
current_revision = module.active_revision(current)
assert current_revision is not None
assert module.revision_number(current_revision) >= module.MIN_SUPPORTED_REVISION
module.normalize(apply=False)
module.assert_contract()
print(f"presentation revision parser {current_revision} test passed")
