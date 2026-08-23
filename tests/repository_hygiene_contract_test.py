#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

retired_paths = (
    ".github/workflows/provider-rebuild-offline.yml",
    ".github/workflows/permanent-lab-branch-guard.yml",
    ".github/workflows/docs-branch-policy-cleanup.yml",
    ".github/workflows/core-media-normalize-main.yml",
    ".github/workflows/final-gate-observer.yml",
    ".github/workflows/final-repository-cleanup-once.yml",
    ".github/workflows/core-reapply-diagnostic-once.yml",
    ".github/workflows/finalization-explicit-launcher-temp.yml",
    ".github/triggers/final-native-client-validation-v2",
    ".github/triggers/native-corpus-device-lab",
    ".github/triggers/permanent-android-real-client",
    ".github/triggers/permanent-real-client-labs",
    "automation/permanent-lab-branches.json",
    "scripts/apply_playback_integrity_upgrade.py",
    "scripts/diagnose_reapply_fixed_point_once.py",
    "scripts/harden_core_fixed_point_normalizer_once.py",
    "scripts/provider_patches/purstream_tv_identity_v3.py",
    "scripts/provider_patches/purstream_tv_identity_impl_v3.py",
    "scripts/provider_patches/purstream_exact_tv_v2.py",
    "scripts/provider_patches/purstream_bridge.py",
    "scripts/migrate_tv_hardening_5_20_39.py",
    "tests/purstream_core_presentation_pipeline_test.py",
)
for rel in retired_paths:
    assert not (ROOT / rel).exists(), f"retired path resurrected: {rel}"

# The rebuild hardening is permanent now; future normalization must never depend
# on a deleted one-shot migration.
materializer = ROOT / "scripts/materialize_core_fixed_point_hardening.py"
assert materializer.is_file()
provider_safety = (ROOT / "scripts/normalize_provider_rebuild_safety.py").read_text(encoding="utf-8")
assert "materialize_core_fixed_point_hardening.py" in provider_safety
assert "harden_core_fixed_point_normalizer_once.py" not in provider_safety

brain = (ROOT / ".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")
assert "publish-repair-proposal:" not in brain
assert "brain-repair/proposals" not in brain
assert 'BRANCH="brain-learning/proposals"' in brain

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

print("repository hygiene contract passed: main-only code workflow, permanent Core hardening, no retired one-shots")
