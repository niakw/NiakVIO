#!/usr/bin/env python3
"""Read-only audit of the exact 96 published Provider v3 bytes; never reconstructs."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
from provider_patch_blocks import decode_managed_data, validate_managed_fixes

ROOT=Path(__file__).resolve().parents[1]
def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def canon(v): return str(v or "").strip().casefold()

manifest=load(ROOT/"manifest.json"); overrides=load(ROOT/"provider-overrides.json"); material=load(ROOT/"provider-v3-materialization.json")
rows=manifest.get("scrapers") or []; reports=material.get("providers") or []
assert len(rows)==96 and len(reports)==96, (len(rows),len(reports))
rb={canon(r.get("provider")):r for r in reports if isinstance(r,dict)}
patches=overrides.get("provider_patches") or {}; seen=set(); agg=hashlib.sha256()
for row in rows:
    pid=canon(row.get("id")); assert pid and pid not in seen, pid; seen.add(pid)
    rel=str(row.get("filename") or ""); path=ROOT/rel
    assert rel.startswith("providers/") and path.is_file(), (pid,rel)
    raw=path.read_bytes(); sha=hashlib.sha256(raw).hexdigest()
    assert path.name==f"{pid}-{sha[:16]}.js", (pid,path.name,sha[:16])
    rep=rb.get(pid); assert rep and rep.get("file")==rel and rep.get("sha256")==sha, pid
    agg.update(pid.encode("utf-8")); agg.update(bytes.fromhex(sha))
    text=raw.decode("utf-8")
    assert text.count("/* BEGIN NIAKVIO_PROVIDER */")==1 and text.count("/* END NIAKVIO_PROVIDER */")==1, pid
    assert text.rstrip().endswith("/* END NIAKVIO_PROVIDER */"), pid
    ids=validate_managed_fixes(text)
    comp=re.sub(r"[^A-Z0-9_.:-]+","_",pid.upper()).strip("_.:-"); cfg=f"PROVIDER.{comp}.CONFIG.V1"
    assert cfg in ids, pid
    first_core=next((i for i,x in enumerate(ids) if x.startswith("CORE.")),len(ids))
    assert all(x.startswith("PROVIDER.") for x in ids[:first_core]), (pid,ids)
    assert all(x.startswith("CORE.") for x in ids[first_core:]), (pid,ids)
    data=decode_managed_data(text,cfg); assert canon(data.get("providerId"))==pid, pid
    expected=str((patches.get(pid) or {}).get("official_site") or "").rstrip("/")
    if expected: assert str(data.get("officialSite") or "").rstrip("/")==expected, pid
    dsha=hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    assert rep.get("providerDataSha256")==dsha, pid
assert set(rb)==seen
assert material.get("providerCount")==96 and material.get("expectedProviderCount")==96
assert material.get("generation")==agg.hexdigest(), (material.get("generation"),agg.hexdigest())
print("PROVIDER_V3_STATIC_AUDIT_OK providers=96 reconstruction=false")
