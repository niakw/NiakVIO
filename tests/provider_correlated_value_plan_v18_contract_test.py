from pathlib import Path

root = Path(__file__).resolve().parents[1]
base = (root / "scripts/provider_base_store.py").read_text(encoding="utf-8")
recovery = (root / "scripts/recover_provider_routes_from_upstreams.py").read_text(encoding="utf-8")
materializer = (root / "scripts/materialize_provider_v3_all.py").read_text(encoding="utf-8")

for needle in (
    "NIAKVIO_PROVIDER_BASE_CORRELATED_VALUE_PLAN_V18",
    "async function _resolveProviderValuePlan",
    "function _spv18ProviderIdFromJson",
    "function _spv18ProviderIdFromHtml",
    "url: _spv17CurrentResponseUrl(url, base)",
    "providerValueStreams = await _resolveProviderValuePlan",
    "NIAKVIO_PROVIDER_CORRELATED_VALUE_SEMANTIC_LANE_V18_5",
    "function _spv185PlanLaneAllowed",
    'if (type === "series" || type === "show" || type === "other") type = "tv";',
    'return lanes.includes(type);',
):
    assert needle in base, needle

for needle in (
    "ROUTE_RECOVERY_CORRELATED_VALUE_PLAN_V18",
    "def _positive_provider_value_plans",
    'row.get("providerValueCorrelation") is True',
    'patch["provider_value_plan"]',
    'model["providerValuePlan"]',
):
    assert needle in recovery, needle

for needle in (
    "PROVIDER_CORRELATED_VALUE_PLAN_V18",
    '"providerValuePlan"',
    'patch.get("provider_value_plan")',
):
    assert needle in materializer, needle

# V18 must remain capability/dataflow-driven. Check the inserted V18 resolver and
# recovery sections rather than unrelated historical code elsewhere in the files.
base_v18 = base.split("/* NIAKVIO_PROVIDER_BASE_CORRELATED_VALUE_PLAN_V18 */", 1)[1].split(
    "async function _resolveSearchRequestPlan", 1
)[0].lower()
recovery_v18 = recovery.split("# ROUTE_RECOVERY_CORRELATED_VALUE_PLAN_V18", 1)[1].split(
    "def apply_recovery", 1
)[0].lower()
for token in (
    "animekai",
    "movies4u",
    "frenchstream",
    "mugiwara",
    "french-stream.one",
    "fs23.lol",
):
    assert token not in base_v18, token
    assert token not in recovery_v18, token

# Core owns explicit provider transport aliases before ProviderBase executes.
# V18.5 proof-plan semanticTypes therefore stay canonical and cannot silently
# cross-select TV and anime lanes.
lane_v18 = base.split("/* NIAKVIO_PROVIDER_CORRELATED_VALUE_SEMANTIC_LANE_V18_5 */", 1)[1].split(
    "function _spv184Trace", 1
)[0]
assert 'return lanes.includes(type);' in lane_v18
assert 'type === "series" || type === "show" || type === "other"' in lane_v18
assert 'semantic.includes("anime")' not in lane_v18
assert 'type === "tv" && lanes.includes("anime")' not in lane_v18
assert 'type === "anime" && lanes.includes("tv")' not in lane_v18

print("provider correlated value plan V18/V18.5 contract tests passed")
