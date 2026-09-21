#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/resolve_provider_hubs.py"
spec=importlib.util.spec_from_file_location("hubresolver",SCRIPT)
assert spec and spec.loader
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

doc="""
<section>
  <h3>Movie Embed</h3>
  <code>https://vidfast.to/embed/movie/{id}</code>
  <h3>TV Show Embed</h3>
  <code>https://vidfast.to/embed/tv/{id}/{season}/{episode}</code>
  <p>Example: https://vidfast.to/embed/movie/986056</p>
  <p>Foreign docs: https://evil.example/embed/movie/{id}</p>
</section>
"""
routes=module.discover_documented_routes("https://vidfast.to",doc)
assert routes==[
    "/embed/movie/{id}",
    "/embed/tv/{id}/{season}/{episode}",
],routes

# Documentation is prior-only: fixture/example URLs without placeholders are ignored.
assert "/embed/movie/986056" not in routes

source=(ROOT/"scripts/build_brain_repair_experience.py").read_text(encoding="utf-8")
runtime=(ROOT/"scripts/adaptive_runtime/runtime_repair.py").read_text(encoding="utf-8")
assert '"documented_routes"' in source
assert '"documented_routes"' in runtime
print("provider documented route discovery contract ok")
