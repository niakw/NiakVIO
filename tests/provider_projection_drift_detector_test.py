#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"detect_provider_projection_drift.py"
spec=importlib.util.spec_from_file_location("projection_drift",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

from provider_patch_blocks import render_managed_fix

assert mod.config_fix_id("anime-sama")=="PROVIDER.ANIME-SAMA.CONFIG.V1"
assert mod.diff_keys({"a":1,"b":2},{"a":1,"b":3,"c":4})==["b","c"]

with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    (root/"providers").mkdir()
    (root/"scripts/provider_patches").mkdir(parents=True)
    (root/"automation").mkdir()

    (root/"manifest.json").write_text(json.dumps({
        "scrapers":[{"id":"alpha","filename":"providers/alpha.js","name":"Alpha","supportedTypes":["movie"]}]
    })+"\n",encoding="utf-8")
    (root/"provider-overrides.json").write_text(json.dumps({
        "provider_patches":{"alpha":{"provider_lego_scripts":["scripts/provider_patches/alpha.py"]}},
        "provider_capabilities":{"alpha":{"strategy":"html_scraper"}},
    })+"\n",encoding="utf-8")
    (root/"automation/provider-v3-static-knowledge.json").write_text(json.dumps({
        "legacyProviderJsExecuted":False,
        "upstreamJsExecuted":False,
        "providers":{"alpha":{"model":{}}},
    })+"\n",encoding="utf-8")
    (root/"scripts/provider_patches/alpha.py").write_text(
        'MANAGED_FIX_ID = "PROVIDER.ALPHA.RUNTIME.V1"\n',
        encoding="utf-8",
    )

    stale="\n".join([
        render_managed_fix(
            "PROVIDER.ALPHA.CONFIG.V1",
            'const NIAKVIO_PROVIDER_MODEL={};',
            data={"providerId":"alpha","officialSite":"https://old.example"},
        ),
        "/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */",
        render_managed_fix("CORE.TEST.V1",'const X=1;',data={"scope":"test"}),
    ])
    (root/"providers/alpha.js").write_text(stale,encoding="utf-8")

    old=(mod.ROOT,mod.MANIFEST,mod.OVERRIDES,mod.STATIC,mod.active_provider_ids,
         mod.normalize_anime_transport_compatibility,mod.provider_model,mod.build_provider_data_model)
    try:
        mod.ROOT=root
        mod.MANIFEST=root/"manifest.json"
        mod.OVERRIDES=root/"provider-overrides.json"
        mod.STATIC=root/"automation/provider-v3-static-knowledge.json"
        mod.active_provider_ids=lambda:{"alpha"}
        mod.normalize_anime_transport_compatibility=lambda entry:None
        mod.provider_model=lambda *_args,**_kwargs:{"knownSite":"https://new.example"}
        mod.build_provider_data_model=lambda *_args,**_kwargs:{"providerId":"alpha","officialSite":"https://new.example"}

        report=mod.detect()
        assert report["providers"]==["alpha"],report
        row=report["rows"][0]
        assert "provider-data-drift" in row["reasons"],row
        assert "declared-lego-drift" in row["reasons"],row
        assert row["changedKeys"]==["officialSite"],row
        assert row["missingFixIds"]==["PROVIDER.ALPHA.RUNTIME.V1"],row

        current="\n".join([
            render_managed_fix(
                "PROVIDER.ALPHA.CONFIG.V1",
                'const NIAKVIO_PROVIDER_MODEL={};',
                data={"providerId":"alpha","officialSite":"https://new.example"},
            ),
            render_managed_fix(
                "PROVIDER.ALPHA.RUNTIME.V1",
                'const RUNTIME=1;',
                data={"runtimeFamily":"alpha"},
            ),
            "/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */",
            render_managed_fix("CORE.TEST.V1",'const X=1;',data={"scope":"test"}),
        ])
        (root/"providers/alpha.js").write_text(current,encoding="utf-8")
        assert mod.detect()["providerCount"]==0,mod.detect()
    finally:
        (mod.ROOT,mod.MANIFEST,mod.OVERRIDES,mod.STATIC,mod.active_provider_ids,
         mod.normalize_anime_transport_compatibility,mod.provider_model,mod.build_provider_data_model)=old

print("provider projection drift detector tests passed")
