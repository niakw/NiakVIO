#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
wf=(ROOT/".github/workflows/provider-waf-browser-session.yml").read_text(encoding="utf-8")
import json

architecture=(ROOT/"automation/provider-v3-architecture.json")
validation=(ROOT/"VALIDATION.json")
arch_md=(ROOT/"ARCHITECTURE.md").read_text(encoding="utf-8")
machine=json.loads(architecture.read_text(encoding="utf-8"))
validation_machine=json.loads(validation.read_text(encoding="utf-8"))

assert machine["schema_version"] >= 24
oracle=machine["network_oracle"]
assert oracle["macbridge_repository"] == "niakw/NiakGH-MacBridge"
assert oracle["primary_residential_oracle"] == "tailscale-residential-exit"
assert "optional" in oracle["macbridge_role"]
assert "indeterminate" in oracle["oracle_unavailable_policy"]
assert "tailscale residential browser/client profiles" in oracle["evidence_precedence"]
assert oracle["require_non_github_replay_for_network_failures"] is True
assert oracle["provider_mutation_requires_cross_environment_evidence_when_network_ambiguous"] is True
assert oracle["provider_disable_requires_cross_environment_evidence_when_network_ambiguous"] is True
assert oracle["domain_mutation_requires_cross_environment_evidence_when_network_ambiguous"] is True
assert oracle["deterministic_tests_do_not_require_macbridge"] is True
assert "403" in oracle["triggers"] and "dns" in oracle["triggers"]

assert validation_machine["schema_version"] >= 82
net=validation_machine["network_origin_validation"]
assert net["github_only_network_failure_is_provider_failure"] is False
assert net["residential_crosscheck_required_before_provider_or_domain_failure"] is True
assert "NiakGH-MacBridge" in net["residential_oracles"]
assert net["macbridge_required_when"] == ["operator_explicitly_requires_mac_user_network_comparison"]
assert "Tailscale" in net["residential_oracle_choice"]
assert "MacBridge" in net["residential_oracle_choice"]
assert "defer provider/domain mutation" in net["oracle_exhaustion_policy"]
assert "Tailscale residential browser/client profiles" in net["stronger_evidence_precedence"]
assert "deterministic_code_contracts" in net["macbridge_not_required_for"]

assert "Oracle réseau résidentiel indépendant" in arch_md
assert "échec réseau GitHub-hosted seul" in arch_md
assert "exact-byte native playback > full provider replay résidentiel" in arch_md
assert "Tailscale" in arch_md

macbridge_evidence=json.loads((ROOT/"automation/macbridge-network-oracle-latest.json").read_text(encoding="utf-8"))
assert macbridge_evidence["role"] == "residential-network-contradiction-oracle"
assert macbridge_evidence["policy"]["githubOnlyNetworkFailureMayNotDisableProvider"] is True
assert macbridge_evidence["policy"]["networkAmbiguityRequiresResidentialReplay"] is True
assert macbridge_evidence["observations"]["hianime"]["residentialRedirect"] == "https://hianime.fm/"
assert macbridge_evidence["observations"]["purstream"]["directResidential"] == "dns-failure"


required=[
    "id-token: write",
    "TS_OAUTH_CLIENT_ID: ${{ secrets.TS_OAUTH_CLIENT_ID }}",
    "TS_AUDIENCE: ${{ secrets.TS_AUDIENCE }}",
    "TS_EXIT_NODE: ${{ secrets.TS_EXIT_NODE }}",
    "TS_TAG_NAME: ${{ secrets.TS_TAG_NAME }}",
    "Normalize private Tailscale CI tag",
    'raw="${TS_TAG_NAME:-niakvio-ci}"',
    '*) normalized="tag:$raw" ;;',
    "TS_ACTION_TAG=%s",
    "tailscale/github-action@064b10558093f38325e838ddea35486bdc6b1d5c",
    "oauth-client-id: ${{ env.TS_OAUTH_CLIENT_ID }}",
    "audience: ${{ env.TS_AUDIENCE }}",
    "args: --accept-dns=false",
    'scripts/verify_waf_exit_route.py select --exit-node "$TS_EXIT_NODE" --attempts 3',
    "tag:niakvio-ci -> autogroup:internet policy",
    "Capture GitHub egress baseline before Tailscale",
    "WAF_EGRESS_STATE=$state",
    "baseline-egress-unavailable",
    "id: tailscale_connect",
    "continue-on-error: true",
    "timeout-minutes: 4",
    "steps.tailscale_connect.outcome == 'success'",
    "id: select_residential_exit",
    "id: residential_probe",
    "scripts/verify_waf_exit_route.py baseline",
    "scripts/verify_waf_exit_route.py verify",
    "scripts/verify_waf_exit_route.py clear",
    "failure_reason=exit-egress-unverified",
    "--unavailable-reason \"$reason\"",
    "tailscale-connect-failed",
    "exit-node-unavailable",
    "residential-probe-failed",
    "scripts/merge_waf_network_profiles.py",
    "--status automation/provider-census-status.json",
    "Resolve explicit transport target cohort",
    "push-triggered WAF qualification requires targetProviders",
    "targeted WAF cohort is capped at 12",
    "FIELD_WAF_EXPLICIT_TARGETS",
    "WAF_ATTEMPTS=2",
    "WAF_WORKERS=4",
    "Merge targeted refresh into complete WAF evidence ledger",
    "scripts/merge_targeted_waf_refresh.py",
]
for needle in required:
    assert needle in wf, f"missing Tailscale WAF contract: {needle}"

assert "for attempt in 1 2 3 4 5" not in wf
for forbidden in (
    "oauth-secret:",
    "ifconfig.me",
    "api.ipify.org",
    "icanhazip",
    "curl -s https://ip",
    "tailscale status --json",
    "tailscale ping --timeout",
    "log-mode:",
    'echo "$TS_EXIT_NODE"',
):
    assert forbidden not in wf, f"privacy/security regression: {forbidden}"

baseline=wf.index("Reprobe persisted WAF lanes on GitHub-hosted network")
egress_baseline=wf.index("Capture GitHub egress baseline before Tailscale")
connect=wf.index("Connect ephemeral Tailscale diagnostic node")
activate=wf.index("Select private residential exit node")
residential=wf.index("Reprobe WAF lanes through private residential exit")
merge=wf.index("Merge residential exit evidence without node identity")
assert baseline < egress_baseline < connect < activate < residential < merge
assert wf.count("verify_waf_exit_route.py baseline") == 1

print("Tailscale residential WAF workflow contract passed")

assert wf.count("--network-report provider-v3-quick-yield.json") == 2

# WAF/Tailscale is now its own explicit transport lane. Full/sharded census
# may still serialize census work, but they no longer own the canonical WAF
# latest and must not block residential qualification.
temp=(ROOT/".github/workflows/temp-current-bytes-full-provider-census.yml").read_text(encoding="utf-8")
sharded=(ROOT/".github/workflows/provider-census-sharded.yml").read_text(encoding="utf-8")
repair=(ROOT/".github/workflows/provider-recognition-repair-v6.yml").read_text(encoding="utf-8")
assert "group: provider-waf-transport-main" in wf
assert "cancel-in-progress: true" in wf
assert "group: provider-census-waf-main" in temp
assert "cancel-in-progress: true" in temp
assert "group: provider-census-" in sharded
assert "'routine' || 'proof' }}-main" in sharded
assert "group: provider-census-waf-main" not in sharded
assert "cancel-in-progress: false" in sharded
assert "group: provider-repair-main-v3" in repair, repair[:600]
assert "cancel-in-progress: ${{ github.event_name == 'push' }}" in repair, repair[:600]
assert "workflow_dispatch:" in temp
assert "FIELD_REPAIR_CANONICAL_LEDGER_STALE" in repair
assert "FIELD_REPAIR_CANONICAL_LEDGER_SKIPPED" in repair
assert "FIELD_REPAIR_FRESH_CENSUS_DISPATCH" in repair
assert "gh workflow run temp-current-bytes-full-provider-census.yml" in repair
assert "gh workflow run provider-waf-browser-session.yml --ref main" not in temp
assert "gh workflow run provider-waf-browser-session.yml --ref main" not in sharded
assert "Prepare integrated Repair WAF/network qualification" in repair
assert "if: ${{ github.ref == 'refs/heads/main' }}" in wf

assert "FIELD_REPAIR_SUPERSEDED_EARLY" in repair

# WAF remains explicit: manual or a dedicated trigger-file push only. Ordinary
# repository pushes still cannot start transport qualification.
assert "workflow_dispatch:" in wf
header=wf.split("permissions:",1)[0]
assert "\n  push:" in header
assert "'.github/triggers/provider-waf-browser-session'" in header

# A Repair run may survive concurrent evidence/docs state commits only when the
# committed-only materialization classifier proves zero provider input drift.
# Provider/Core drift remains fail-closed.
assert "repair-early-concurrent-scope.json" in repair
assert '--committed-only' in repair
assert 'FIELD_REPAIR_SUPERSEDED_EARLY neutral=true mode=none' in repair
assert 'FIELD_REPAIR_SUPERSEDED_EARLY neutral=false mode=$provider_drift_mode' in repair
