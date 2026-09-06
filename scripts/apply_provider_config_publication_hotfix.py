#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REAPPLY = ROOT / "scripts" / "reapply_published_overrides.py"
VALIDATOR = ROOT / "scripts" / "validate_published_provider_config.py"
TEST = ROOT / "tests" / "final_published_provider_config_test.py"
MEMORY = ROOT / "MEMORY.md"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)


def patch_reapply() -> None:
    text = REAPPLY.read_text(encoding="utf-8")
    if "FINAL_PROVIDER_CONFIG_INVARIANT_V1" in text:
        print("reapply Provider CONFIG publication fix already applied")
        return

    text = replace_once(
        text,
        '''from provider_base_store import (\n    CLEAN_RECONSTRUCTION_EXCLUDED_PATCH_SCRIPTS,\n    is_clean_reconstructed,\n    is_clean_reconstruction_candidate,\n    resolve_base,\n    resolve_runtime_base,\n)\n''',
        '''from provider_base_store import (\n    CLEAN_RECONSTRUCTION_EXCLUDED_PATCH_SCRIPTS,\n    build_provider_data_model,\n    canonical_id,\n    compose_provider_bundle,\n    is_clean_reconstructed,\n    is_clean_reconstruction_candidate,\n    resolve_base,\n    resolve_runtime_base,\n)\nfrom materialize_provider_v3_all import provider_model as build_structured_provider_model\n''',
        "provider_base_store import",
    )
    text = replace_once(
        text,
        'OVERRIDES = ROOT / "provider-overrides.json"\nVERSION_FLOORS = ROOT / "provider-version-floors.json"\n',
        'OVERRIDES = ROOT / "provider-overrides.json"\nSTATIC_KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"\nVERSION_FLOORS = ROOT / "provider-version-floors.json"\n',
        "static knowledge constant",
    )
    text = replace_once(
        text,
        '''def validate_artifact(data: bytes, provider_id: str) -> None:\n    with tempfile.NamedTemporaryFile(suffix=".js", delete=False, dir=ROOT) as handle:\n''',
        '''def assert_final_provider_config(data: bytes, provider_id: str) -> None:\n    # FINAL_PROVIDER_CONFIG_INVARIANT_V1\n    text = data.decode("utf-8", errors="strict")\n    if "NIAKVIO_PROVIDER_BASE_OWNED_V3" not in text:\n        return\n    canonical = canonical_id(provider_id)\n    fix_id = f"PROVIDER.{canonical.upper()}.CONFIG.V1"\n    start = f"/* STARTFIX:{fix_id} */"\n    close = f"/* CLOSEFIX:{fix_id} */"\n    declaration = "const NIAKVIO_PROVIDER_MODEL = Object.freeze("\n    if text.count(start) != 1 or text.count(close) != 1:\n        raise ValueError(\n            f"{provider_id}: final published Provider CONFIG cardinality invalid "\n            f"start={text.count(start)} close={text.count(close)}"\n        )\n    if text.count(declaration) != 1:\n        raise ValueError(\n            f"{provider_id}: final published NIAKVIO_PROVIDER_MODEL declaration "\n            f"count={text.count(declaration)} expected=1"\n        )\n    if not (text.index(start) < text.index(declaration) < text.index(close)):\n        raise ValueError(f"{provider_id}: Provider model declaration escaped CONFIG Lego")\n    if text.count("/* BEGIN NIAKVIO_PROVIDER */") != 1 or text.count("/* END NIAKVIO_PROVIDER */") != 1:\n        raise ValueError(f"{provider_id}: final Provider envelope cardinality invalid")\n\n\ndef validate_artifact(data: bytes, provider_id: str) -> None:\n    assert_final_provider_config(data, provider_id)\n    with tempfile.NamedTemporaryFile(suffix=".js", delete=False, dir=ROOT) as handle:\n''',
        "final artifact config validator",
    )
    text = replace_once(
        text,
        '''PUBLICATION_CONTRACT_FILES = (\n    "scripts/reapply_published_overrides.py",\n    "scripts/apply_provider_overrides.py",\n''',
        '''PUBLICATION_CONTRACT_FILES = (\n    "scripts/reapply_published_overrides.py",\n    "scripts/apply_provider_overrides.py",\n    "scripts/provider_base_store.py",\n    "scripts/materialize_provider_v3_all.py",\n    "automation/provider-v3-static-knowledge.json",\n''',
        "publication contract inputs",
    )
    text = replace_once(
        text,
        '''        if not public_path.is_file():\n            return False, f"missing-public-bundle:{provider_id}"\n        actual_public_sha = hashlib.sha256(public_path.read_bytes()).hexdigest()\n''',
        '''        if not public_path.is_file():\n            return False, f"missing-public-bundle:{provider_id}"\n        try:\n            assert_final_provider_config(public_path.read_bytes(), provider_id)\n        except ValueError as exc:\n            return False, f"final-provider-config:{provider_id}:{exc}"\n        actual_public_sha = hashlib.sha256(public_path.read_bytes()).hexdigest()\n''',
        "fixed point final CONFIG gate",
    )
    text = replace_once(
        text,
        '''    override_config, removed_hooks = sanitize_provider_hooks(load_overrides(), ROOT)\n    override_config, removed_origins = sanitize_capability_origins(override_config)\n    if not args.check:\n''',
        '''    override_config, removed_hooks = sanitize_provider_hooks(load_overrides(), ROOT)\n    override_config, removed_origins = sanitize_capability_origins(override_config)\n    static_knowledge = json.loads(STATIC_KNOWLEDGE.read_text(encoding="utf-8"))\n    static_rows = static_knowledge.get("providers")\n    if not isinstance(static_rows, dict):\n        raise ValueError("Provider v3 static knowledge providers map required")\n    structured_patches = override_config.get("provider_patches")\n    structured_capabilities = override_config.get("provider_capabilities")\n    if not isinstance(structured_patches, dict) or not isinstance(structured_capabilities, dict):\n        raise ValueError("structured Provider DATA maps required for publication")\n    if not args.check:\n''',
        "load structured publication data",
    )
    text = replace_once(
        text,
        '''        clean_v2_base = runtime_base_is_clean_v2(\n            provider_id,\n            provider_provenance,\n            provider_base_path,\n        )\n        if clean_v2_base:\n            # Clean ProviderBase v3 deliberately excludes historical adaptive source\n            # patches. Never replay intentionally absent legacy migrators here.\n            domain_revision_records = []\n''',
        '''        clean_v2_base = runtime_base_is_clean_v2(\n            provider_id,\n            provider_provenance,\n            provider_base_path,\n        )\n        if clean_v2_base:\n            patch_row = structured_patches.get(provider_id)\n            capability_row = structured_capabilities.get(provider_id)\n            static_row = static_rows.get(provider_id)\n            if not isinstance(patch_row, dict) or not isinstance(capability_row, dict) or not isinstance(static_row, dict):\n                raise ValueError(f"{provider_id}: structured DATA incomplete during final publication")\n            structured_model = build_structured_provider_model(\n                provider_id, patch_row, capability_row, static_row\n            )\n            provider_data = build_provider_data_model(\n                provider_id,\n                entry,\n                known_site=structured_model.get("knownSite"),\n                provider_model=structured_model,\n            )\n            # Recreate the same Base + DATA envelope used by the authoritative\n            # materializer before Provider/Core Lego are replayed. Publication\n            # must never execute a clean ProviderBase without its CONFIG model.\n            migrated = compose_provider_bundle(provider_id, migrated, provider_data)\n            # Clean ProviderBase v3 deliberately excludes historical adaptive source\n            # patches. Never replay intentionally absent legacy migrators here.\n            domain_revision_records = []\n''',
        "compose CONFIG before final Core",
    )
    REAPPLY.write_text(text, encoding="utf-8")


def write_validator() -> None:
    content = '''#!/usr/bin/env python3\nfrom __future__ import annotations\n\nimport argparse\nimport json\nimport sys\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\nsys.path.insert(0, str(ROOT / "scripts"))\nfrom provider_base_store import canonical_id\nfrom provider_patch_blocks import decode_managed_data\n\nDECL = "const NIAKVIO_PROVIDER_MODEL = Object.freeze("\n\ndef validate_bundle(text: str, provider_id: str) -> None:\n    canonical = canonical_id(provider_id)\n    if "NIAKVIO_PROVIDER_BASE_OWNED_V3" not in text:\n        return\n    fix_id = f"PROVIDER.{canonical.upper()}.CONFIG.V1"\n    start = f"/* STARTFIX:{fix_id} */"\n    close = f"/* CLOSEFIX:{fix_id} */"\n    if text.count(start) != 1 or text.count(close) != 1:\n        raise ValueError(f"{canonical}: CONFIG Lego cardinality start={text.count(start)} close={text.count(close)}")\n    if text.count(DECL) != 1:\n        raise ValueError(f"{canonical}: NIAKVIO_PROVIDER_MODEL declaration count={text.count(DECL)}")\n    if not (text.index(start) < text.index(DECL) < text.index(close)):\n        raise ValueError(f"{canonical}: model declaration outside CONFIG Lego")\n    model = decode_managed_data(text, fix_id)\n    if canonical_id(str(model.get("providerId") or "")) != canonical:\n        raise ValueError(f"{canonical}: CONFIG providerId mismatch")\n    if text.count("/* BEGIN NIAKVIO_PROVIDER */") != 1 or text.count("/* END NIAKVIO_PROVIDER */") != 1:\n        raise ValueError(f"{canonical}: Provider envelope cardinality invalid")\n\ndef validate_manifest(path: Path, expected: int) -> None:\n    payload = json.loads(path.read_text(encoding="utf-8"))\n    rows = [row for row in payload.get("scrapers") or [] if isinstance(row, dict)]\n    if len(rows) != expected:\n        raise ValueError(f"manifest provider count={len(rows)} expected={expected}")\n    seen = set()\n    for row in rows:\n        provider_id = canonical_id(str(row.get("id") or ""))\n        if not provider_id or provider_id in seen:\n            raise ValueError(f"invalid/duplicate provider id: {provider_id!r}")\n        seen.add(provider_id)\n        relative = str(row.get("filename") or "")\n        if not relative.startswith("providers/"):\n            raise ValueError(f"{provider_id}: unsafe final filename {relative!r}")\n        bundle = (ROOT / relative).resolve()\n        if not bundle.is_file() or (ROOT / "providers").resolve() not in bundle.parents:\n            raise ValueError(f"{provider_id}: final bundle missing/unsafe {relative}")\n        validate_bundle(bundle.read_text(encoding="utf-8"), provider_id)\n    print(f"final published Provider CONFIG tests passed providers={len(rows)}")\n\ndef main() -> int:\n    parser = argparse.ArgumentParser()\n    parser.add_argument("--manifest", type=Path, default=ROOT / "manifest.json")\n    parser.add_argument("--expected", type=int, default=96)\n    args = parser.parse_args()\n    validate_manifest(args.manifest.resolve(), args.expected)\n    return 0\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'''
    VALIDATOR.write_text(content, encoding="utf-8")


def write_test() -> None:
    content = '''#!/usr/bin/env python3\nfrom __future__ import annotations\n\nimport importlib.util\nimport json\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\nspec = importlib.util.spec_from_file_location("final_config", ROOT / "scripts" / "validate_published_provider_config.py")\nmodule = importlib.util.module_from_spec(spec)\nassert spec and spec.loader\nspec.loader.exec_module(module)\nmodule.validate_manifest(ROOT / "manifest.json", 96)\nmanifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))\nrow = next(item for item in manifest["scrapers"] if isinstance(item, dict) and str(item.get("filename") or "").startswith("providers/"))\ntext = (ROOT / row["filename"]).read_text(encoding="utf-8")\nbroken = text.replace("const NIAKVIO_PROVIDER_MODEL = Object.freeze(", "const NIAKVIO_BROKEN_MODEL = Object.freeze(", 1)\ntry:\n    module.validate_bundle(broken, str(row.get("id") or ""))\nexcept ValueError:\n    pass\nelse:\n    raise AssertionError("missing Provider model declaration was not rejected")\nprint("final published Provider CONFIG regression test passed")\n'''
    TEST.write_text(content, encoding="utf-8")


def update_memory() -> None:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    version = str(manifest.get("version") or "unknown")
    text = MEMORY.read_text(encoding="utf-8")
    marker = "## Final-byte Provider CONFIG invariant — 2026-09-06"
    section = f'''\n\n{marker}\n\n- Current corrected manifest generation at this checkpoint: **`{version}`**.\n- `NIAKVIO_PROVIDER_MODEL` is NiakVIO-owned structured runtime DATA, materialized as exactly one `PROVIDER.<ID>.CONFIG.V1`; ProviderBase and Source Plan v4 (`_spv4Family`) may reference it but ProviderBase itself must remain DATA-free.\n- Regression found in `5.21.34`: the authoritative materializer correctly composed Base + CONFIG + Lego, but `reapply_published_overrides.py` restarted final publication from the clean ProviderBase and replayed Core without re-running `compose_provider_bundle()`. This produced final bundles that referenced `NIAKVIO_PROVIDER_MODEL` without defining it.\n- Final publication now reuses the same structured `provider_model -> build_provider_data_model -> compose_provider_bundle` path as the 96-provider materializer before replaying Provider/Core Lego.\n- A final-manifest 96/96 gate validates the actual hashed JS referenced by `manifest.json`, not only `provider-v3-materialization.json`: one CONFIG START/CLOSE pair, one `NIAKVIO_PROVIDER_MODEL = Object.freeze(...)`, matching providerId, safe final path and Provider envelope. A missing model is publication-fatal.\n- Identity remains dual-source: valid TMDB **or IMDb** input is accepted; TMDB enrichment verifies/enriches identity but cannot invalidate a valid IMDb input. Episodic IMDb suffixes such as `tt11198330:3:1` retain season/episode.\n- `series` remains a Nuvio transport alias for canonical `tv`; it belongs in `supportedTypes`, never in `canonicalSupportedTypes`.\n'''
    if marker in text:
        head = text.split(marker, 1)[0].rstrip()
        text = head + section
    else:
        text = text.rstrip() + section
    MEMORY.write_text(text.rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--memory-only", action="store_true")
    args = parser.parse_args()
    if args.memory_only:
        update_memory()
        return 0
    patch_reapply()
    write_validator()
    write_test()
    print("Provider CONFIG publication source hotfix applied")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
