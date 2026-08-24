#!/usr/bin/env python3
from __future__ import annotations

# Harmless checkpoint: this test path intentionally triggers the isolated Brain learning lab.
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/brain-learning-lab.yml"
DISCOVERY = ROOT / "scripts/discover_candidates.py"
APPLY = ROOT / "scripts/apply_provider_overrides.py"
GLOBAL_PRESENTATION = ROOT / "scripts/provider_patches/global_stream_presentation_v1.py"
GLOBAL_FACTS = ROOT / "scripts/provider_patches/global_stream_facts_v1.py"
READER_REPAIR = ROOT / "scripts/build_native_reader_brain_repair.py"
RUN_SANDBOX = ROOT / "scripts/run_brain_learning_sandbox.py"
OVERRIDES = ROOT / "provider-overrides.json"
CATALOG = ROOT / "provider_catalog.json"
MANIFEST = ROOT / "manifest.json"
PATCH_ROOT = ROOT / "scripts/provider_patches"


def norm(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def referenced_patch_scripts(config: dict) -> set[str]:
    output: set[str] = set()
    for profile in (config.get("patch_profiles") or {}).values():
        if isinstance(profile, dict) and profile.get("patch_script"):
            output.add(str(profile["patch_script"]))
    for provider in (config.get("provider_patches") or {}).values():
        if not isinstance(provider, dict):
            continue
        if provider.get("patch_script"):
            output.add(str(provider["patch_script"]))
        for value in provider.get("patch_scripts") or []:
            if str(value).strip():
                output.add(str(value))
    playback = config.get("playback_integrity_policy") or {}
    for key in ("global_discovery_hooks", "pre_media_discovery_hooks", "post_media_discovery_hooks"):
        for value in playback.get(key) or []:
            if str(value).strip():
                output.add(str(value))
    for policy_name in ("catalogue_resolution_policy", "media_enrichment_policy"):
        policy = config.get(policy_name) or {}
        if policy.get("global_discovery_hook"):
            output.add(str(policy["global_discovery_hook"]))
    return output


def main() -> int:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    discovery = DISCOVERY.read_text(encoding="utf-8")
    apply_source = APPLY.read_text(encoding="utf-8")
    presentation_source = GLOBAL_PRESENTATION.read_text(encoding="utf-8")
    facts_source = GLOBAL_FACTS.read_text(encoding="utf-8")
    sandbox_source = RUN_SANDBOX.read_text(encoding="utf-8")
    overrides = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    # The Brain cron must always reconstruct the complete catalogue, including
    # disabled providers which still need repair/re-evaluation evidence.
    assert "schedule:" in workflow and "cron:" in workflow, "Brain learning cron disappeared"
    assert "python scripts/resolve_provider_hubs.py --apply --mode quick --include-disabled" in workflow
    assert "python scripts/discover_candidates.py --require-all-upstreams" in workflow
    assert "validate-stage-against-catalog.mjs --catalog provider_catalog.json --stage staging/candidates.json" in workflow
    assert "python scripts/run_brain_learning_sandbox.py --stage staging" in workflow
    assert "ref: main" in workflow, "scheduled Brain must run from trusted production main"

    # Scheduled Brain uses the same Quick Brain implementation as normal repair,
    # not a second reduced skill engine.
    assert "import run_adaptive_quick_repair as quick" in sandbox_source
    assert "apply_overrides(canonical_id(upstream_id), data)" in discovery
    assert "GLOBAL_STREAM_PRESENTATION" in apply_source
    assert '"scope": "global_stream_presentation"' in apply_source

    # Stream facts/badges are a Core-wide contract. No provider-specific facts
    # adapter may be required for Purstream or any other provider.
    assert GLOBAL_FACTS.is_file()
    assert "NUVIO_GLOBAL_STREAM_FACTS_V1" in facts_source
    assert "FACTS_PATH" in presentation_source
    assert "global_stream_facts_v1.py" in presentation_source
    assert "_apply_facts(text, context)" in presentation_source
    assert not (PATCH_ROOT / "purstream_stream_facts_v1.py").exists()

    # Every patch/profile referenced by production configuration must physically
    # exist. This catches a skill being renamed/fixed without wiring the cron.
    scripts = referenced_patch_scripts(overrides)
    assert scripts, "no repair/discovery patch scripts configured"
    missing = sorted(path for path in scripts if not (ROOT / path).is_file())
    assert not missing, "configured patch scripts missing: " + ", ".join(missing)

    # Native-reader Brain hypotheses are also a real skill registry. Every mapped
    # skill must be supported by apply_skill and backed by a current module.
    reader = load_module(READER_REPAIR, "brain_cron_reader_repair")
    skills = sorted({skill for values in reader.HYPOTHESIS_SKILLS.values() for skill in values})
    assert skills, "native reader Brain exposes no repair skills"
    for skill in skills:
        expected = PATCH_ROOT / f"{skill}.py"
        assert expected.is_file(), f"native reader Brain skill is missing: {skill}"
    apply_skill_source = READER_REPAIR.read_text(encoding="utf-8")
    for skill in skills:
        assert skill in apply_skill_source, f"native reader Brain skill is not wired: {skill}"

    # provider_catalog is the authority. Every projected provider must be present
    # in its manifest order and every published general scraper must map back to a
    # canonical provider. This is the static all-provider coverage fence.
    providers = [row for row in catalog.get("providers") or [] if isinstance(row, dict)]
    catalog_ids = {norm(row.get("canonicalId")) for row in providers if norm(row.get("canonicalId"))}
    assert catalog_ids, "provider catalog is empty"
    general_order = {norm(value) for value in (catalog.get("manifestOrder") or {}).get("general") or [] if norm(value)}
    vf_order = {norm(value) for value in (catalog.get("manifestOrder") or {}).get("vf") or [] if norm(value)}
    projected_general = {
        norm(row.get("canonicalId")) for row in providers
        if norm(row.get("canonicalId")) and bool((row.get("projections") or {}).get("general"))
    }
    projected_vf = {
        norm(row.get("canonicalId")) for row in providers
        if norm(row.get("canonicalId")) and bool((row.get("projections") or {}).get("vf"))
    }
    assert projected_general == general_order, (
        "general provider projection/order mismatch",
        sorted(projected_general - general_order),
        sorted(general_order - projected_general),
    )
    assert projected_vf == vf_order, (
        "VF provider projection/order mismatch",
        sorted(projected_vf - vf_order),
        sorted(vf_order - projected_vf),
    )

    manifest_ids = {
        norm(row.get("id")) for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and norm(row.get("id"))
    }
    assert manifest_ids == general_order, (
        "published manifest no longer covers the complete general provider projection",
        sorted(general_order - manifest_ids),
        sorted(manifest_ids - general_order),
    )

    # No native-reader observation may directly disable a provider. Reader repair
    # can only generate bounded candidates after cross-client confirmation.
    reader_source = READER_REPAIR.read_text(encoding="utf-8")
    assert '"nativeReaderFailureNeverDirectlyDisablesProvider": True' in reader_source
    assert '"anyHealthyClientPreventsGlobalDisable": True' in reader_source
    assert '"tvIsPrimaryRetentionSignal": True' in reader_source
    assert '"globalProviderDisableCandidates": 0' in reader_source

    print(
        "Brain cron full coverage tests passed "
        f"({len(catalog_ids)} providers, {len(scripts)} configured patch scripts, "
        f"{len(skills)} native reader Brain skills)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
