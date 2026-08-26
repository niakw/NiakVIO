#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

retired_paths = (
    ".github/workflows/provider-rebuild-offline.yml",
    ".github/workflows/engine-regression-offline.yml",
    ".github/workflows/permanent-lab-branch-guard.yml",
    ".github/workflows/docs-branch-policy-cleanup.yml",
    ".github/workflows/core-media-normalize-main.yml",
    ".github/workflows/final-gate-observer.yml",
    ".github/workflows/final-repository-cleanup-once.yml",
    ".github/workflows/core-reapply-diagnostic-once.yml",
    ".github/workflows/finalization-explicit-launcher-temp.yml",
    ".github/workflows/provider-fixed-point-audit.yml",
    ".github/workflows/provider-fixed-point-diagnostic.yml",
    ".github/workflows/core-runtime-domain-invocation-fix-once.yml",
    ".github/workflows/finalize-zink-desktop-once.yml",
    ".github/workflows/external-code-audit-refresh.yml",
    ".github/workflows/main-only-policy.yml",
    ".github/workflows/actions-maintenance.yml",
    ".github/workflows/native-provider-loading-compat.yml",
    ".github/triggers/offline-engine-regression",
    ".github/triggers/final-native-client-validation-v2",
    ".github/triggers/native-corpus-device-lab",
    ".github/triggers/permanent-android-real-client",
    ".github/triggers/permanent-real-client-labs",
    "automation/permanent-lab-branches.json",
    "scripts/apply_playback_integrity_upgrade.py",
    "scripts/diagnose_reapply_fixed_point_once.py",
    "scripts/harden_core_fixed_point_normalizer_once.py",
    "scripts/audit_provider_fixed_point.py",
    "sitecustomize.py",
    "scripts/sitecustomize.py",
    "scripts/provider_patches/purstream_tv_identity_v3.py",
    "scripts/provider_patches/purstream_tv_identity_impl_v3.py",
    "scripts/provider_patches/purstream_exact_tv_v2.py",
    "scripts/provider_patches/purstream_bridge.py",
    "scripts/migrate_tv_hardening_5_20_39.py",
    "tests/purstream_core_presentation_pipeline_test.py",
)
for rel in retired_paths:
    assert not (ROOT / rel).exists(), f"retired path resurrected: {rel}"

# One-shot/temporary workflows are migration machinery, not permanent repository
# architecture. Once a migration lands on main its workflow must disappear; keeping
# the naming contract generic prevents a new forgotten self-cleaning workflow from
# silently becoming part of the long-lived CI surface.
workflow_dir = ROOT / ".github/workflows"
retired_workflow_names = (
    "external-code-audit-refresh.yml",
    "main-only-policy.yml",
    "actions-maintenance.yml",
    "native-provider-loading-compat.yml",
)
for workflow in workflow_dir.iterdir():
    if not workflow.is_file() or workflow.suffix not in {".yml", ".yaml"}:
        continue
    name = workflow.name.lower()
    assert not any(
        marker in name
        for marker in ("-once.", "_once.", "-temp.", "_temp.", "-temporary.", "_temporary.")
    ), f"temporary/one-shot workflow must not remain on main: {workflow.relative_to(ROOT)}"
    source = workflow.read_text(encoding="utf-8")
    executable_source = "\n".join(
        line for line in source.splitlines() if not line.lstrip().startswith("#")
    )
    for retired_name in retired_workflow_names:
        assert retired_name not in executable_source, (
            f"permanent workflow still executes/references retired workflow {retired_name}: "
            f"{workflow.relative_to(ROOT)}"
        )

materializer = ROOT / "scripts/materialize_core_fixed_point_hardening.py"
assert materializer.is_file()
provider_safety = (ROOT / "scripts/normalize_provider_rebuild_safety.py").read_text(encoding="utf-8")
assert "materialize_core_fixed_point_hardening.py" in provider_safety
assert "harden_core_fixed_point_normalizer_once.py" not in provider_safety

for rel in (
    "scripts/classify_native_reader_ownership.py",
    "scripts/merge_native_reader_learning_failures.py",
    "scripts/build_native_reader_learning_summary.py",
    "tests/native_reader_ownership_policy_test.py",
):
    assert (ROOT / rel).is_file(), f"permanent reader ownership contract missing: {rel}"

# Core materialization validates only JavaScript syntax. It must neither execute
# upstream-derived providers nor guess runtime exports from obfuscated source text;
# workers/native Labs own runtime and getStreams validation.
validator = (ROOT / "scripts/validate_provider_artifact.cjs").read_text(encoding="utf-8")
assert "node:path" in validator
assert "--check" in validator
assert "timeout: 5000" in validator
assert "env: {}" in validator
assert "mode=syntax-only" in validator
assert "execution=false" in validator
assert "require(file)" not in validator
assert "runInContext" not in validator
assert "vm.createContext" not in validator
assert "getStreamsContracts" not in validator

brain = (ROOT / ".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")
assert "publish-repair-proposal:" not in brain
assert "brain-repair/proposals" not in brain
assert 'BRANCH="brain-learning/proposals"' in brain
assert "--baseline-health brain-learning-input/baseline-health.json" in brain
assert "tests/native_reader_ownership_policy_test.py" in brain

hygiene = (ROOT / ".github/workflows/repository-hygiene.yml").read_text(encoding="utf-8")
assert "brain-repair/proposals" in hygiene
assert "git push origin --delete" in hygiene
assert "main|brain-learning/proposals" in hygiene

install = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
assert "final-native-client-validation-v2.yml" not in install
assert "native-android-route-reader.yml" in install
assert "native-desktop-reader-acceptance.yml" in install

readme = (ROOT / "README.md").read_text(encoding="utf-8")
architecture = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
for stale in (
    "lab/tv-real",
    "lab/desktop-mobile-real",
    "provider-rebuild-offline.yml",
    "engine-regression-offline.yml",
):
    assert stale not in readme, f"README resurrected retired reference: {stale}"
    assert stale not in architecture, f"ARCHITECTURE resurrected retired reference: {stale}"

assert "`main` : unique branche de code" in readme
assert "## 22. Labs natifs sur `main`" in architecture
assert "brain-learning/proposals" in readme
assert "brain-learning/proposals" in architecture

codeql = (ROOT / ".github/workflows/codeql.yml").read_text(encoding="utf-8")
assert "javascript-typescript" in codeql
assert "python" in codeql
assert "security-extended" in codeql
assert "db488ddef3bf6cb639b32c2e9a7c0a7ea8271d28" in codeql

print("repository hygiene contract passed: main-only code workflow, permanent Core/reader hardening, syntax-only provider validation, no retired one-shots or executable workflow references")
