#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
FILES={
    "allwish":"scripts/provider_patches/allwish_runtime_v1.py",
    "animesalt":"scripts/provider_patches/animesalt_runtime_v1.py",
    "flemmix":"scripts/provider_patches/flemmix_runtime_v1.py",
    "mallumv":"scripts/provider_patches/mallumv_runtime_v1.py",
    "moviesmod":"scripts/provider_patches/moviesmod_runtime_v1.py",
}

for provider,rel in FILES.items():
    src=(ROOT/rel).read_text(encoding="utf-8")
    assert "o&&(o.title||o.name)" in src, (provider,"object title fallback missing")
    assert "year" in src, (provider,"year fallback missing")
    wrapper=src.split("WRAPPER = r'''",1)[1].split("'''",1)[0].replace("CONFIG_PLACEHOLDER","{}")
    subprocess.run(["node","-e","new Function(process.argv[1]);",wrapper],check=True)

assert "if(q&&q.title)" in (ROOT/FILES["allwish"]).read_text(encoding="utf-8")
assert "if(q&&q.title)" in (ROOT/FILES["animesalt"]).read_text(encoding="utf-8")
assert "if(q&&q.title)" in (ROOT/FILES["flemmix"]).read_text(encoding="utf-8")
assert "if(!m&&q&&q.title)" in (ROOT/FILES["mallumv"]).read_text(encoding="utf-8")
assert "if(q&&q.title)" in (ROOT/FILES["moviesmod"]).read_text(encoding="utf-8")
print("Provider canonical title fallback contract passed")
