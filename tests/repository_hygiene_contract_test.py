#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

for rel in (
    ".github/workflows/tmp-trigger-pending-finalizers.yml",
    ".github/workflows/tmp-apply-stream-presentation-v11.yml",
    ".github/workflows/tmp-optimize-tv-reader.yml",
    "scripts/apply_tv_reader_optimization.py",
    "automation/tv-reader-migration-failure.txt",
):
    assert not (ROOT / rel).exists(), f"retired one-shot resurrected: {rel}"

for rel in (
    "scripts/native_tv_route_checkpoint.py",
    "scripts/build_native_reader_retest_manifest.py",
    "tests/native_tv_route_resume_test.py",
    "scripts/normalize_stream_presentation_v12.py",
    "automation/native-stream-presentation-contract.json",
    "scripts/audit_repository_tree.py",
):
    assert (ROOT / rel).is_file(), f"durable contract missing: {rel}"

hygiene = (ROOT / ".github/workflows/repository-hygiene.yml").read_text(encoding="utf-8")
for token in (
    "pull-requests: read",
    "open_pr_branches",
    "Active pull-request branch allowed temporarily",
    "main|brain-learning/proposals",
    "git push origin --delete",
):
    assert token in hygiene, token

gate = (ROOT / ".github/workflows/github-actions-gate.yml").read_text(encoding="utf-8")
for token in ("actionlint", "audit_repository_tree.py", "repository_hygiene_contract_test.py"):
    assert token in gate, token

scanner_path = ROOT / "scripts/audit_repository_tree.py"
spec = importlib.util.spec_from_file_location("audit_repository_tree", scanner_path)
assert spec and spec.loader
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)
assert scanner.has_conflict_block("title\n=======\nbody\n") is False
assert scanner.has_conflict_block("<<<<<<< ours\na\n=======\nb\n>>>>>>> theirs\n") is True

core_policy = (ROOT / "scripts/normalize_core_media_policy.py").read_text(encoding="utf-8")
assert "normalize_stream_presentation_v12" in core_policy
assert "presentation=global_core_v12" in core_policy

presentation = (ROOT / "scripts/provider_patches/global_stream_presentation_v1.py").read_text(encoding="utf-8")
assert "all-providers-client-projected-badge-emoji-tmdb-v12" in presentation
assert 'out.description=visible;out.size=visible;out.quality="";out.language=""' in presentation

validator = (ROOT / "scripts/validate_provider_artifact.cjs").read_text(encoding="utf-8")
assert "mode=syntax-only" in validator
assert "execution=false" in validator
assert "require(file)" not in validator

codeql = (ROOT / ".github/workflows/codeql.yml").read_text(encoding="utf-8")
assert "javascript-typescript" in codeql
assert "python" in codeql
assert "security-extended" in codeql

print("repository hygiene contract passed: active PR branches preserved, one-shots retired, V12 + sharded TV durable")
