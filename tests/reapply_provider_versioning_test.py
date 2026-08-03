#!/usr/bin/env python3
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec=spec_from_file_location('reapply',ROOT/'scripts/reapply_published_overrides.py')
mod=module_from_spec(spec); spec.loader.exec_module(mod)
assert mod.bump_provider_version('1.0.0')=='1.0.1'
assert mod.bump_provider_version('2.9.99')=='2.9.100'
assert mod.bump_provider_version('bad')=='1.0.1'
print('reapplied provider versioning tests passed')
