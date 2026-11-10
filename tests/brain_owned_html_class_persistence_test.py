#!/usr/bin/env python3
"""Generic Brain HTML class-token repair survives ProviderBase-owned Lego materialization.

This is a scoped generated-code proof on the *existing* nested HTML fixture.
No provider-specific override, no real terminal playback and no census promotion.
"""
from __future__ import annotations
import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from apply_provider_overrides import _canonicalize_owned_html_class_tokens  # noqa: E402

spec=importlib.util.spec_from_file_location(
    "shared_4k_parser_oracle",ROOT/"scripts/provider_patches/4khdhub_runtime_v1.py"
)
assert spec and spec.loader
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
wrapper=module.WRAPPER
FIX="PROVIDER.DEMO.RUNTIME.V1"
BEGIN=f"/* STARTFIX:{FIX} */"
END=f"/* CLOSEFIX:{FIX} */"
upstream="/* BEGIN NIAKVIO_PROVIDER */\nconst stable=1;\n"
downstream="\n/* STARTFIX:CORE.STREAM_IDENTITY.V1 */stableCore()/* CLOSEFIX:CORE.STREAM_IDENTITY.V1 */\n/* END NIAKVIO_PROVIDER */"
original=upstream+BEGIN+"\n"+wrapper+"\n"+END+downstream
repaired=_canonicalize_owned_html_class_tokens(original,FIX)
assert repaired!=original,"Brain's generic CSS matcher was not materialized"
assert repaired.startswith(upstream+BEGIN),"Changed bytes outside owned block before start"
assert repaired.endswith(END+downstream),"Changed bytes outside owned block after end"
assert repaired.count("NUVIO_HTML_CLASS_TOKEN_EXACT_V1")==1
assert repaired.index("NUVIO_HTML_CLASS_TOKEN_EXACT_V1") > repaired.index(BEGIN)
assert repaired.index("NUVIO_HTML_CLASS_TOKEN_EXACT_V1") < repaired.index(END)
assert "(?![-_A-Za-z0-9])" in repaired
assert _canonicalize_owned_html_class_tokens(repaired,FIX)==repaired
assert _canonicalize_owned_html_class_tokens(original,"CORE.STREAM_IDENTITY.V1")==original

# Extract exactly the existing response fixture's JS harness.
tree=ast.parse((ROOT/"tests/provider_4khdhub_runtime_behavior_test.py").read_text(encoding="utf-8"))
expr=next(n.value for n in tree.body if isinstance(n,ast.Assign)
          and any(isinstance(t,ast.Name) and t.id=="js" for t in n.targets))
assert isinstance(expr,ast.BinOp) and isinstance(expr.left,ast.BinOp)
prefix,suffix=expr.left.left.value,expr.right.value
cfg={"base":"https://4khdhub.one","maxStreams":8,"ua":"NiakVIO-Test"}

def replay(code: str) -> dict:
    source=prefix+code.replace("CONFIG_PLACEHOLDER",json.dumps(cfg,separators=(",",":")))+suffix
    with tempfile.TemporaryDirectory(prefix="brain-class-owned-") as tmp:
        script=Path(tmp)/"probe.cjs"
        script.write_text(source,encoding="utf-8")
        run=subprocess.run(["node",str(script)],cwd=ROOT,capture_output=True,text=True,timeout=22)
        assert run.returncode==0,run.stderr[-1500:]
        return json.loads(run.stdout.strip().splitlines()[-1])
before=replay(wrapper)
body=repaired.split(BEGIN,1)[1].split(END,1)[0]
after=replay(body)
assert not before["movie"] and not before["tv"],before
assert len(after["movie"])==1 and len(after["tv"])==1,after
assert after["movie"][0]["url"]=="https://media.workers.dev/colony.mkv"
assert after["tv"][0]["url"]=="https://media.workers.dev/bb-s01e01.mkv"
assert "S01E01" in after["tv"][0]["title"]
print("FIELD_BRAIN_HTML_CLASS_OWNED_LEGO original_movie=0 original_tv=0 "
      "repaired_movie=1 repaired_tv=1 managed_block_only=true "
      "fixed_point=true core_unchanged=true live_media_validated=false")
