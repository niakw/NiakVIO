#!/usr/bin/env python3
from __future__ import annotations

# Harmless checkpoint: this test path intentionally triggers the isolated Brain learning lab.
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/brain-learning-lab.yml"
AVAILABILITY_WORKFLOW = ROOT / ".github/workflows/availability.yml"
DISCOVERY = ROOT / "scripts/discover_candidates.py"
APPLY = ROOT / "scripts/apply_provider_overrides.py"
GLOBAL_PRESENTATION = ROOT / "scripts/provider_patches/global_stream_presentation_v1.py"
GLOBAL_FACTS = ROOT / "scripts/provider_patches/global_stream_facts_v1.py"
READER_REPAIR = ROOT / "scripts/build_native_reader_brain_repair.py"
RUN_SANDBOX = ROOT / "scripts/run_brain_learning_sandbox.py"
LEARNING_QUEUE = ROOT / "scripts/run_brain_learning_queue.py"
QUICK_REPAIR = ROOT / "scripts/run_adaptive_quick_repair.py"
LEARNING_LAB = ROOT / "engine_v2/scripts/learning-lab.mjs"
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
    availability_workflow = AVAILABILITY_WORKFLOW.read_text(encoding="utf-8")
    discovery = DISCOVERY.read_text(encoding="utf-8")
    apply_source = APPLY.read_text(encoding="utf-8")
    presentation_source = GLOBAL_PRESENTATION.read_text(encoding="utf-8")
    facts_source = GLOBAL_FACTS.read_text(encoding="utf-8")
    sandbox_source = RUN_SANDBOX.read_text(encoding="utf-8")
    queue_source = LEARNING_QUEUE.read_text(encoding="utf-8")
    quick_source = QUICK_REPAIR.read_text(encoding="utf-8")
    learning_source = LEARNING_LAB.read_text(encoding="utf-8")
    overrides = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    # The Brain cron must always reconstruct the complete catalogue, including
    # disabled providers which still need repair/re-evaluation evidence.
    assert "schedule:" in workflow and "cron:" in workflow, "Brain learning cron disappeared"
    assert "python scripts/run_brain_learning_queue.py" in workflow, "canonical adaptive Learning queue disappeared"
    assert "python scripts/select_brain_learning_target.py" not in workflow, "obsolete single-target selector is executing again"
    assert "--budget-minutes 60" in workflow, "global one-hour Learning budget disappeared"
    experiment_block = workflow[workflow.index("  experiment:"):workflow.index("\n  publish-learning:")]
    assert "timeout-minutes: 120" in experiment_block, (
        "Brain job timeout must cover full-catalogue observation plus the independent one-hour Learning queue"
    )
    assert "--reserve-minutes 5" in workflow, "Learning finalization reserve disappeared"
    assert "--stream-safety-cap 2" in workflow, "bounded quick Learning stream cap disappeared"
    assert "TARGET_PROVIDER: ${{ inputs.target_provider || '' }}" in workflow, "manual provider override disappeared"
    assert 'args+=(--provider "$TARGET_PROVIDER")' in workflow, "manual provider override is not delegated to the canonical queue"
    assert "provider_dns_preflight.mjs" not in workflow, "DNS diagnostics belong to the daily domain observer, not Learning"
    assert "python scripts/discover_candidates.py --require-all-upstreams" in workflow
    assert "validate-stage-against-catalog.mjs --catalog provider_catalog.json --stage staging/candidates.json" in workflow
    assert "ref: main" in workflow, "scheduled Brain must run from trusted production main"
    assert "publish_proposal:" in workflow, "watchdog/manual proposal input disappeared"
    assert "publish-repair-proposal:" in workflow, "validated Brain PR job disappeared"
    assert "brain-repair/proposal" in workflow, "single Brain repair PR branch disappeared"
    assert "publish-architecture-proposal:" in workflow, "Brain self-evolution PR job disappeared"
    assert "brain-architecture/proposal" in workflow, "dedicated Brain architecture PR branch disappeared"
    assert "scripts/build_brain_architecture_proposal.py" in workflow
    assert "engine_v2/config/brain-self-evolution.json" in workflow
    assert "brain-architecture-proposal.md" in workflow
    assert "--queue-summary brain-sandbox/health-output/learning-queue-summary.json" in workflow
    assert "--queue-state brain-sandbox/health-output/learning-queue-state.json" in workflow
    assert "--learning-queue-state brain-sandbox/health-output/learning-queue-state.json" in workflow
    assert "github.event_name == 'schedule'" in workflow
    assert "github.event.inputs.publish_proposal == 'true'" in workflow
    assert "Import latest weekly FULL native Lab diagnostics into Learning memory" in workflow
    assert 'gh run list --workflow "$workflow" --event schedule --status completed' in workflow
    assert "merge_native_reader_backlog.py" in workflow
    assert "merge_native_reader_learning_failures.py" in workflow
    assert "native-tv-route-representative-*" in workflow
    assert "native-mobile-android-routes-*" in workflow
    assert "native-mobile-ios-routes-*" in workflow
    assert "native-desktop-reader-*-routes-*" in workflow
    assert "gh workflow run native-mobile-android-reader.yml" not in workflow
    assert "gh workflow run native-mobile-ios-reader.yml" not in workflow
    assert "gh workflow run native-desktop-reader-acceptance.yml" not in workflow
    assert "brain-learning-watchdog:" in availability_workflow
    assert "brain-learning-lab.yml" in availability_workflow
    assert "publish_proposal=true" in availability_workflow
    assert "20 * 60 * 60" in availability_workflow
    assert 'if [ "$((10#$HOUR))" -lt 4 ]' in availability_workflow

    # Scheduled Learning uses the same repair engine as normal Quick repair, but
    # the canonical queue owns provider scheduling, route recovery, retries,
    # rotating fixtures, multi-device Labs and cross-day resume.
    assert "import run_adaptive_quick_repair as quick" in sandbox_source
    assert "NUVIO_BRAIN_PLANNER_MODE" in quick_source
    assert 'return "learning" if mode == "learning" else "quick"' in quick_source
    assert "_base_matching_profiles" in sandbox_source
    assert "explorationShare" in sandbox_source
    assert "learningExplorationApplied" in sandbox_source
    assert "_restore_positive_skills" in sandbox_source
    assert 'return list(dict.fromkeys(kept))' in sandbox_source, "one repair pass may evaluate multiple compatible fix profiles"

    assert 'str(SCRIPTS / "run_brain_learning_sandbox.py")' in queue_source
    assert '"--max-rounds", "0"' in queue_source, "queue must let the sandbox explore until its global deadline"
    assert "while time.time() < work_deadline:" in queue_source, "provider repair loop is no longer deadline-driven"
    assert "seen_method_sets" in queue_source, "Learning must stop repeating an exhausted method set"
    assert "retryProviders" in queue_source and "pendingProviders" in queue_source, "cross-day queue persistence disappeared"
    assert "interleave(" in queue_source, "retry work must not starve unseen providers"
    assert '"tv,desktop,mobile"' not in queue_source, "legacy per-command Lab CLI returned"
    assert "nuvio_client_lab_session.cjs" in queue_source, "Learning warm Lab session disappeared"
    assert "subprocess.Popen(" in queue_source, "Learning must keep one Lab process alive"
    assert '"clients": ["tv", "desktop", "mobile"]' in queue_source
    assert '"provider_timeout_ms": 12000' in queue_source
    assert '"retry_provider_timeouts": False' in queue_source
    assert '"max_settings_profiles": 1' in queue_source
    assert '"max_streams_per_runtime": max(1, min(int(stream_cap), 2))' in queue_source
    assert '"playback_timeout_ms": 5000' in queue_source
    assert 'summary["warmSession"] = True' in queue_source
    assert '"coreIsAuthoritative": False' in queue_source, "Core evidence must remain a hypothesis in Learning"
    assert "hiddenFailureProviders" in queue_source, "Core/Lab contradictions must be persisted"
    assert "routeEvidenceCount" in queue_source, "route discovery must emit evidence depth"
    assert 'str(SCRIPTS / "resolve_provider_hubs.py")' in queue_source
    assert 'str(SCRIPTS / "resolve_provider_hub_search_fallback.py")' in queue_source
    assert "needs_route_search" in queue_source, "route discovery must remain conditional per provider"
    assert "refresh_stage_routes(stage, work_deadline)" in queue_source, "newly discovered routes must be reprojected into the Lab stage"

    policy_source = (ROOT / "engine_v2" / "config" / "brain-policy.json").read_text(encoding="utf-8")
    assert '"targetProvidersPerRun": "time_budgeted_queue"' in policy_source
    assert '"clientSelection": "tv_desktop_mobile_for_scheduled_learning"' in policy_source
    assert '"streamSampling": "all_returned_streams_with_safety_cap"' in policy_source
    assert '"retryPolicy": "continue_with_new_hypotheses_until_global_deadline_or_no_new_method"' in policy_source
    assert '"maxRepairRounds"' not in policy_source, "obsolete one-round Learning limit returned"
    assert '"selfArchitectureAudit": true' in policy_source
    assert '"selfArchitectureChanges": "review_only_pr_with_allowlisted_policy_changes_and_structural_change_plan"' in policy_source

    # Learning memory and discovery capabilities remain shared and sanitized.
    assert 'state.get("learnedSkills")' in sandbox_source
    assert "mergeLearnedSkills(previous.learnedSkills, currentSkills)" in learning_source
    assert "yandex.com/search/?text=" in (ROOT / "scripts" / "resolve_provider_hubs.py").read_text(encoding="utf-8")
    assert "html.duckduckgo.com/html/?q=" in (ROOT / "scripts" / "resolve_provider_hubs.py").read_text(encoding="utf-8")
    assert "learnedSkills," in learning_source
    # Upstream JavaScript is discovery knowledge only. The old pipeline applied
    # overrides directly to downloaded upstream bytes; that would recreate the
    # legacy architecture we are deliberately migrating all 95 providers away from.
    assert "apply_overrides(provider_id, data)" not in discovery
    assert '"upstream_code_role": "knowledge-only"' in discovery
    assert '"upstream_code_executed": False' in discovery
    assert '"legacy_provider_js_executed_for_reconstruction": False' in discovery
    assert '"new-niakvio-clean-seed"' in discovery
    assert "build_clean_provider_seed(" in discovery
    assert "clean_provider_model(" in discovery
    assert "GLOBAL_STREAM_PRESENTATION" in apply_source
    assert '"scope": "global_stream_presentation"' in apply_source
    assert "GLOBAL_MEDIA_TYPE_RESOLUTION" in apply_source
    assert '"scope": "global_media_type_resolution"' in apply_source
    assert "global_media_type_resolution_v1.py" in apply_source

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
