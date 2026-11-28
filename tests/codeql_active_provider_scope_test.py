#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"scripts/prune_codeql_generated_providers.py"
spec=importlib.util.spec_from_file_location("codeql_scope",SOURCE)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    (root/"providers").mkdir()
    for name in ("active-a.js","active-b.js","retained-old.js"):
        (root/"providers"/name).write_text("// fixture\n",encoding="utf-8")
    (root/"provider-disabled").mkdir()
    (root/"provider-disabled"/"disabled.js").write_text("// retained disabled fixture\n",encoding="utf-8")
    manifests={
        "manifest.json":["providers/active-a.js","provider-disabled/disabled.js"],
        "vf/manifest.json":["../providers/active-b.js"],
        "no-anime/manifest.json":["../providers/active-a.js"],
        "vf-no-anime/manifest.json":["../providers/active-b.js"],
    }
    for relative,names in manifests.items():
        path=root/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(
            json.dumps({"scrapers":[{"id":str(i),"filename":name} for i,name in enumerate(names)]}),
            encoding="utf-8",
        )
    assert mod.published_provider_paths(root)=={"providers/active-a.js","providers/active-b.js"}
    count,removed=mod.prune_workspace(root)
    assert count==2 and removed==1
    assert sorted(path.name for path in (root/"providers").glob("*.js"))==["active-a.js","active-b.js"]

with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    (root/"providers").mkdir()
    (root/"providers"/"active.js").write_text("// fixture\n",encoding="utf-8")
    for relative in mod.MANIFESTS:
        path=root/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        filename="providers/active.js" if relative=="manifest.json" else "../providers/active.js"
        path.write_text(json.dumps({"scrapers":[{"id":"a","filename":filename}]}),encoding="utf-8")
    bad=root/"vf/manifest.json"
    bad.write_text(json.dumps({"scrapers":[{"id":"escape","filename":"../../outside.js"}]}),encoding="utf-8")
    try:
        mod.published_provider_paths(root)
    except ValueError as exc:
        assert "escaped repository" in str(exc)
    else:
        raise AssertionError("manifest traversal escaped CodeQL active-provider scope")

print("CodeQL active published-provider projection passed")
