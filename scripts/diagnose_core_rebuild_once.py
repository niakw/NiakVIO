#!/usr/bin/env python3
"""Temporary one-shot diagnostic for Core byte-idempotence; never writes providers."""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "scripts"))

import apply_provider_overrides as apo
from provider_engine_normalizer import sanitize_provider_hooks, strip_foreign_provider_wrappers
from provider_purification import purify_bytes
from reapply_published_overrides import (
    strip_unproven_adaptive_language,
    reapply_adaptive_domain_revision,
    reapply_adaptive_runtime_revision,
)

PROVIDER = "anime-sama"
MARKER = "NUVIO_GLOBAL_CORE_START_BOUNDARY_V1"


def validate(label: str, data: bytes) -> None:
    text = data.decode("utf-8", errors="strict")
    indices = {
        "provider_var": text.find("var __provider"),
        "provider_any": text.find("__provider="),
        "module_export": text.find("module.exports=__provider"),
        "module_export_spaced": text.find("module.exports = __provider"),
        "global_export": text.find("globalThis.getStreams"),
        "core_marker": text.find(MARKER),
    }
    print(
        "FIELD_REBUILD_STAGE "
        f"label={label} bytes={len(data)} sha={hashlib.sha256(data).hexdigest()[:16]} "
        + " ".join(f"{key}={value}" for key, value in indices.items())
    )
    with tempfile.NamedTemporaryFile(suffix=".js", delete=False, dir=ROOT) as handle:
        handle.write(data)
        path = Path(handle.name)
    try:
        result = subprocess.run(
            ["node", str(ROOT / "scripts" / "validate_provider_artifact.cjs"), str(path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        detail = " | ".join(v.strip().replace("\n", " :: ") for v in (result.stdout, result.stderr) if v.strip())
        print(f"FIELD_REBUILD_VALIDATE label={label} rc={result.returncode} detail={detail[:1200]}")
    finally:
        path.unlink(missing_ok=True)


def install_patch_trace() -> None:
    native = apo._apply_patch_script
    def traced(text, provider_id, patch_script, options, profile_name):
        before_var = text.find("var __provider")
        before_export = text.find("module.exports=__provider")
        before_len = len(text)
        out = native(text, provider_id, patch_script, options, profile_name)
        after_var = out.find("var __provider")
        after_export = out.find("module.exports=__provider")
        print(
            "FIELD_REBUILD_PATCH "
            f"provider={provider_id} script={patch_script} profile={profile_name or '-'} "
            f"bytes_before={before_len} bytes_after={len(out)} provider_var_before={before_var} "
            f"provider_var_after={after_var} export_before={before_export} export_after={after_export}"
        )
        return out
    apo._apply_patch_script = traced


def transform(data: bytes, config: dict, provenance_row: dict | None, pass_no: int) -> bytes:
    validate(f"p{pass_no}-input", data)
    text, removed = strip_foreign_provider_wrappers(data.decode("utf-8"), PROVIDER, config)
    data = text.encode()
    print(f"FIELD_REBUILD_MUTATION label=p{pass_no}-wrapper-isolation removed={len(removed)}")
    validate(f"p{pass_no}-after-wrapper-isolation", data)

    data, count = strip_unproven_adaptive_language(data)
    print(f"FIELD_REBUILD_MUTATION label=p{pass_no}-adaptive-language removed={count}")
    validate(f"p{pass_no}-after-adaptive-language", data)

    data, records = reapply_adaptive_domain_revision(data)
    print(f"FIELD_REBUILD_MUTATION label=p{pass_no}-adaptive-domain records={len(records)}")
    validate(f"p{pass_no}-after-adaptive-domain", data)

    data, records = apo.apply_overrides(PROVIDER, data, phase="discovery")
    print(f"FIELD_REBUILD_MUTATION label=p{pass_no}-core-overrides records={json.dumps(records, separators=(',', ':'))}")
    validate(f"p{pass_no}-after-core-overrides", data)

    data, records = reapply_adaptive_runtime_revision(data, provenance_row)
    print(f"FIELD_REBUILD_MUTATION label=p{pass_no}-adaptive-runtime records={len(records)}")
    validate(f"p{pass_no}-after-adaptive-runtime", data)

    purified, report = purify_bytes(data)
    print(
        "FIELD_REBUILD_MUTATION "
        f"label=p{pass_no}-purify applied={report.get('applied')} mode={report.get('mode')} "
        f"before={report.get('bytesBefore')} after={report.get('bytesAfter')} fallback={report.get('fallbackReason')}"
    )
    validate(f"p{pass_no}-after-purify", purified)
    return purified


def main() -> int:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    row = next(r for r in manifest["scrapers"] if str(r.get("id", "")).casefold() == PROVIDER)
    source = ROOT / row["filename"]
    provenance = json.loads((ROOT / "PROVENANCE.json").read_text(encoding="utf-8"))
    provenance_row = (provenance.get("providers") or {}).get(PROVIDER)
    config, _ = sanitize_provider_hooks(apo.load_overrides(), ROOT)
    install_patch_trace()

    first = transform(source.read_bytes(), config, provenance_row, 1)
    second = transform(first, config, provenance_row, 2)
    same = first == second
    print(
        f"FIELD_REBUILD_RESULT provider={PROVIDER} fixed_point={str(same).lower()} "
        f"first={hashlib.sha256(first).hexdigest()} second={hashlib.sha256(second).hexdigest()}"
    )
    return 0 if same else 2


if __name__ == "__main__":
    raise SystemExit(main())
