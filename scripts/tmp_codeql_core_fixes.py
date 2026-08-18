#!/usr/bin/env python3
from pathlib import Path


def replace(path: str, old: str, new: str, count: int | None = None) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    found = text.count(old)
    if found == 0:
        raise SystemExit(f"missing replacement anchor in {path}: {old!r}")
    if count is not None and found != count:
        raise SystemExit(f"unexpected replacement count in {path}: {found} != {count}")
    target.write_text(text.replace(old, new), encoding="utf-8")


# The full corpus is a trusted post-publication/main lab. Manual branch diagnostics
# are provided by the targeted workflow.
replace(
    ".github/workflows/native-corpus-device-lab.yml",
    "on:\n  workflow_dispatch:\n  workflow_run:\n",
    "on:\n  workflow_run:\n",
    1,
)

expr = "$" + "{{"

targeted = Path(".github/workflows/native-corpus-device-targeted.yml")
text = targeted.read_text(encoding="utf-8")
target_ref = """      target_ref:
        description: Niakvio ref/SHA to validate
        required: false
        default: main
        type: string
"""
if text.count(target_ref) != 1:
    raise SystemExit("target_ref input anchor mismatch")
text = text.replace(target_ref, "")
text = text.replace(
    f"      target_sha: {expr} steps.resolve.outputs.target_sha }}}}\n",
    "",
)
old_checkout = (
    "      - name: Checkout requested Niakvio generation\n"
    "        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1\n"
    "        with:\n"
    f"          ref: {expr} github.event_name == 'workflow_dispatch' && inputs.target_ref || 'main' }}}}\n"
    "          fetch-depth: 1\n"
)
new_checkout = (
    "      - name: Checkout selected Niakvio generation\n"
    "        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1\n"
    "        with:\n"
    "          fetch-depth: 1\n"
    "          persist-credentials: false\n"
)
if text.count(old_checkout) != 1:
    raise SystemExit("requested checkout anchor mismatch")
text = text.replace(old_checkout, new_checkout)
text = text.replace(
    "      - name: Resolve exact generation, selected devices and accepted clients\n",
    "      - name: Resolve selected devices and accepted clients\n",
)
text = text.replace('          TARGET_SHA="$(git rev-parse HEAD)"\n', "")
text = text.replace('          echo "target_sha=$TARGET_SHA" >> "$GITHUB_OUTPUT"\n', "")
old_downstream = (
    f"          ref: {expr} needs.resolve.outputs.target_sha }}}}\n"
    "          path: niakvio\n"
)
new_downstream = (
    f"          ref: {expr} github.sha }}}}\n"
    "          path: niakvio\n"
    "          persist-credentials: false\n"
)
if text.count(old_downstream) != 1:
    raise SystemExit("targeted downstream target_sha anchor mismatch")
text = text.replace(old_downstream, new_downstream)
if "target_ref" in text or "needs.resolve.outputs.target_sha" in text:
    raise SystemExit("untrusted target ref remains in targeted workflow")
targeted.write_text(text, encoding="utf-8")

# Comment hygiene: retain durable invariants, remove conversational/historical narration.
replace(
    "scripts/promote_candidates.py",
    "            # A transient source download failure must not silently disable a\n"
    "            # previously published local provider.\n",
    "            # A transient source download failure must not disable a published\n"
    "            # local provider.\n",
    1,
)
replace(
    "scripts/provider_dns_preflight.mjs",
    "            // Globalping HTTP options are top-level within measurementOptions.\n"
    "            // The previous nested request object was rejected with HTTP 400.\n",
    "            // Globalping HTTP options are top-level within measurementOptions.\n",
    1,
)
replace(
    "tests/strict_native_identity_guard_test.py",
    "# Same config must be idempotent, while an implementation-revision upgrade must\n"
    "# have stripped the previous V2 block instead of stacking it.\n",
    "# Reapplying the same config is idempotent; implementation upgrades replace\n"
    "# the existing V2 block instead of stacking another copy.\n",
    1,
)
replace(
    "tests/published_overrides_test.py",
    "# references converge. Regression: Coflix was deleted after strict validation,\n"
    "# then the manifest transaction failed because provenance/LKG still referenced\n"
    "# the deleted content-addressed bundle.\n",
    "# references converge.\n",
    1,
)
replace(
    "tests/published_overrides_test.py",
    "# A provider id must not match a longer sibling id while removing stale files.\n"
    "# Regression: validating 4khdhub previously deleted 4khdhubnew because the\n"
    "# cleanup used the broad glob ``4khdhub*.js``.\n",
    "# Stale-file removal must use exact provider-id boundaries so a provider id\n"
    "# cannot match a longer sibling id.\n",
    1,
)
replace(
    "tests/deep_repair_rollback_test.py",
    "# These providers previously received a bad metadata-context repair. The durable\n"
    "# invariant is that the marker never returns and that manifest/provenance/hash\n"
    "# describe the exact current published bytes. Hard-coding an old SHA made this\n"
    "# regression test reject legitimate repository-wide playback hardening.\n",
    "# These published artifacts must never contain the rejected metadata-context\n"
    "# marker. Manifest, provenance and hashes must describe the exact current bytes;\n"
    "# fixed historical SHAs would incorrectly reject legitimate artifact rotation.\n",
    1,
)
replace(
    "tests/native_catalogue_recovery_budget_test.py",
    "# A provider produced by the previous V1 budget revision must upgrade in place,\n"
    "# rather than keeping the overly narrow first-two-search policy forever.\n",
    "# V1-produced providers must upgrade in place rather than retaining the\n"
    "# narrower first-two-search policy.\n",
    1,
)
replace(
    "scripts/promote_candidates.py",
    "    ``base_version`` is a version floor. This prevents an unchanged run from\n"
    "    preserving an obsolete series (for example 5.13.x after the repository has\n"
    "    moved to 5.14.x).\n",
    "    ``base_version`` is a version floor so unchanged runs cannot preserve an\n"
    "    obsolete version series.\n",
    1,
)
replace(
    "scripts/publish_cross_platform_runtime_policy.py",
    "legacy 5.20.27 Android blocks that were based only on missing proof are removed\n"
    "when fresh evidence remains inconclusive. Existing blocks not managed by this\n",
    "Android blocks based only on missing proof are removed when fresh evidence\n"
    "remains inconclusive. Existing blocks not managed by this\n",
    1,
)
replace(
    "scripts/publish_cross_platform_runtime_policy.py",
    "                # legacy Android no-proof policy, whose basis was deliberately\n"
    "                # weaker and is retired by this release.\n",
    "                # Android no-proof blocks are weaker than conclusive runtime\n"
    "                # evidence and are retired once fresh evidence is inconclusive.\n",
    1,
)
