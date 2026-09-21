#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/"scripts"
sys.path.insert(0,str(SCRIPTS))
spec=importlib.util.spec_from_file_location(
    "materialize_clean_provider_reconstruction_self_contained",
    SCRIPTS/"materialize_clean_provider_reconstruction.py",
)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as directory:
    root=Path(directory)
    source=root/"source"
    output=root/"output"
    (source/"provider-bases").mkdir(parents=True)
    output.mkdir()

    demo=b"/* canonical clean provider base */\n"
    demo_sha=hashlib.sha256(demo).hexdigest()
    demo_name=f"demo--base--{demo_sha[:16]}.js"
    (source/"provider-bases"/demo_name).write_bytes(demo)

    existing=b"/* already proposed base */\n"
    existing_sha=hashlib.sha256(existing).hexdigest()
    existing_name=f"existing--base--{existing_sha[:16]}.js"
    (output/existing_name).write_bytes(existing)

    rows={
        "demo":{
            "base_filename":f"provider-bases/{demo_name}",
            "base_sha256":demo_sha,
        },
        "existing":{
            "base_filename":f"provider-bases/{existing_name}",
            "base_sha256":existing_sha,
        },
    }
    copied=mod.materialize_supporting_bases(rows,output,source_root=source)
    assert copied==["demo"], copied
    assert (output/demo_name).read_bytes()==demo
    assert (output/existing_name).read_bytes()==existing

    bad=dict(rows)
    bad["missing"]={
        "base_filename":"provider-bases/missing--base--0000000000000000.js",
        "base_sha256":"0"*64,
    }
    try:
        mod.materialize_supporting_bases(bad,output,source_root=source)
    except ValueError as exc:
        assert "missing=" in str(exc)
    else:
        raise AssertionError("missing provenance base was not rejected")

    (output/demo_name).write_bytes(b"tampered")
    try:
        mod.materialize_supporting_bases(rows,output,source_root=source)
    except ValueError as exc:
        assert "invalid=" in str(exc)
    else:
        raise AssertionError("mismatched provenance base sha was not rejected")

workflow=(ROOT/".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")
assert "brain-learning-output/provider-bases/" in workflow
source=(SCRIPTS/"materialize_clean_provider_reconstruction.py").read_text(encoding="utf-8")
assert "supportingBaseCount" in source
assert "proposal provenance is not self-contained" in source

print("Brain reconstruction proposal self-containment contract passed")
