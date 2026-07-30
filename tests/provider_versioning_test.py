#!/usr/bin/env python3
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = spec_from_file_location("promote_candidates", ROOT / "scripts" / "promote_candidates.py")
module = module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

assert module.provider_entry_version(
    {"version": "1.0.0", "filename": "providers/movix--nuvio--new.js"},
    {"version": "1.0.0", "filename": "providers/movix--nuvio--old.js"},
) == "1.0.1"
assert module.provider_entry_version(
    {"version": "9.9.9", "filename": "providers/same.js"},
    {"version": "1.2.3", "filename": "providers/same.js"},
) == "1.2.3"
print("provider manifest versioning test passed")
