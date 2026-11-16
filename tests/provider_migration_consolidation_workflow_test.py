#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
wf=(ROOT/".github/workflows/provider-migration-consolidation.yml").read_text(encoding="utf-8")

for marker in (
    "Apply deterministic migrations and prove second-pass idempotence",
    "upgrade_provider_route_authority_v5.py",
    "upgrade_provider_external_identity_route_v11_1.py",
    "upgrade_provider_v3_source_plan_v5.py",
    "upgrade_mugiwara_episode_failclosed_v2.py",
    "provider-migration-pass1.diff",
    "provider-migration-pass2.diff",
    "cmp /tmp/provider-migration-pass1.diff /tmp/provider-migration-pass2.diff",
    "migration touched unexpected paths",
    "Persist consolidated migration state",
    'remote="$(git rev-parse origin/main)"',
    'if [ "$remote" != "$GITHUB_SHA" ]',
):
    assert marker in wf,marker

for retired in (
    "repair-anime-semantic-gate-20260914.yml",
    "dle-anime-two-provider-repair-short.yml",
    "french-manga-dle-repair-short.yml",
    "voiranime-homes-dle-repair-short.yml",
    "neko-sama-runtime-v2-short.yml",
    "castle-language-roles-short.yml",
    "kehflix-current-live-short.yml",
    "kehflix-terminal-data-publish-short.yml",
    "voiranime-domain-authority-repair-short.yml",
    "quick-proven-fixes-publish-short.yml",
    "stream-sanitizer-v9-source-short.yml",
    "hls-master-facts-short.yml",
    "provider-parity-short-vod-short.yml",
    "provider-parity-order-bias-short.yml",
    "provider-parity-deep-hls-terminal-short.yml",
    "provider-parity-local-only-publish-short.yml",
):
    assert not (ROOT / ".github/workflows" / retired).exists(), retired

# Consolidation is source/DATA-only. Publication remains owned by the normal
# reconstruction/census lanes so this one-shot workflow cannot bypass current-byte proof.
for forbidden in (
    "materialize_provider_v3_all.py --",
    "git add providers",
    "git add provider-bases",
    "publicationAllowed",
):
    assert forbidden not in wf,forbidden

print("provider migration consolidation workflow contract passed")
