#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import inspect
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str((ROOT/"scripts").resolve()))

probe_path=ROOT/"scripts/probe_bulk_provider_routes.py"
spec=importlib.util.spec_from_file_location("bulk_route_probe_test",probe_path)
probe=importlib.util.module_from_spec(spec); spec.loader.exec_module(probe)

site_probe_path=ROOT/"scripts/probe_provider_site_structure.py"
site_spec=importlib.util.spec_from_file_location("provider_site_structure_test",site_probe_path)
site_probe=importlib.util.module_from_spec(site_spec); site_spec.loader.exec_module(site_probe)

assert site_probe.search_form_routes(
    '<form method="get" action="/index.php"><input name="story"></form>',
    "https://demo.example/",
) == ["/index.php?story={query}"]
assert site_probe.search_form_routes(
    '<form method="get" action="/find"><input name="term"></form>',
    "https://demo.example/",
) == ["/find?term={query}"]
assert site_probe.search_form_routes(
    '<form method="post" action="/search"><input name="q"></form>',
    "https://demo.example/",
) == []
assert site_probe.search_form_routes(
    '<form method="get" action="https://other.example/search"><input name="q"></form>',
    "https://demo.example/",
) == []

fixture={"title":"Interstellar","tmdbId":"157336","mediaType":"movie"}
assert probe.route_pattern("/search?q=",fixture)=="/search?q={query}"
assert probe.route_pattern("/api?m=search&q=",fixture)=="/api?m=search&q={query}"
assert probe.route_pattern("/api/search?term=",fixture)=="/api/search?term={query}"
assert probe.route_pattern("/search/interstellar",fixture)=="/search/{slug}"
common_source=inspect.getsource(probe.probe_common_identity_routes)
for token in ('"/search/{slug}"','"/api/search?q={query}"','f"/watch/{{tmdbId}}"'):
    assert token in common_source, token
assert probe.route_pattern("/title/movie/157336-interstellar",fixture)=="/title/movie/{tmdbId}-{slug}"
assert probe.route_pattern("/api/streams/movie?token=secret&q=",fixture)==""
assert probe.route_pattern("/",fixture)==""
assert probe.route_pattern("/tv/1396?play=true&s=1&e=1", {"title":"Breaking Bad","tmdbId":"1396","mediaType":"tv","season":1,"episode":1}) == "/tv/{tmdbId}?play=true&s={season}&e={episode}"
assert probe.identity_route_candidate("/play?id=254630&type={media}&season={season}&episode={episode}") is False
assert probe.identity_route_candidate("/tv/254630?play=true&s={season}&e={episode}") is False
assert probe.identity_route_candidate("/api/push/subscribe") is False
assert probe.identity_route_candidate("/api/session-handoff/issue") is False
assert probe.identity_route_candidate("/embed/sw.js") is False
assert probe.identity_route_candidate("/series") is False
assert probe.identity_route_candidate("/search") is False
assert probe.identity_route_candidate("/movie/{tmdbId}") is True
assert probe.identity_route_candidate("/search?q={query}") is True
assert probe.identity_route_candidate("/search?s={query}") is True
assert probe._render_route("/search?q={query}", fixture) == "/search?q=Interstellar"
assert probe._render_route("/movie/{tmdbId}", fixture) == "/movie/157336"
assert probe._identity_response(b"<a>Interstellar</a>", fixture, direct_media_route=False) is True
assert probe._identity_response(b'{"tmdb":"157336","stream":"https://cdn.example/x.m3u8"}', fixture, direct_media_route=True) is True
assert probe._identity_response(b"<html>unrelated page</html>", fixture, direct_media_route=False) is False

legacy_model = probe._decode_owned_provider_model(
    '/* NIAKVIO_PROVIDER_BASE_OWNED_V2 */\nconst NIAKVIO_PROVIDER_MODEL = Object.freeze({"providerId":"legacy","officialSite":"https://legacy.example","routes":["/movie/{tmdbId}"]});',
    "PROVIDER.LEGACY.CONFIG.V1",
)
assert legacy_model == {"providerId":"legacy","officialSite":"https://legacy.example","routes":["/movie/{tmdbId}"]}
assert "provider-old" in inspect.getsource(probe.retained_v3_routes)

apply_path=ROOT/"scripts/apply_bulk_provider_route_discovery.py"
apply_spec=importlib.util.spec_from_file_location("bulk_route_apply_test",apply_path)
apply_mod=importlib.util.module_from_spec(apply_spec); apply_spec.loader.exec_module(apply_mod)

selected, standby = apply_mod.select_to_target(
    [
        {"id":"anime-only","scope":"france","types":["anime"],"inventory_score":99,"inventory_rank":1},
        {"id":"movie-tv","scope":"france","types":["movie","tv"],"inventory_score":70,"inventory_rank":20},
        {"id":"movie-only","scope":"france","types":["movie"],"inventory_score":90,"inventory_rank":2},
    ],
    scope="france",
    current={"active":58,"lanes":{"movie":18,"tv":17,"anime":22}},
)
assert [row["id"] for row in selected] == ["movie-tv","movie-only"], selected
assert [row["id"] for row in standby] == ["anime-only"], standby
selected, standby = apply_mod.select_to_target(
    [{"id":"overflow","scope":"global","types":["movie","tv","anime"]}],
    scope="global",
    current={"active":60,"lanes":{"movie":20,"tv":20,"anime":20}},
)
assert selected == [] and [row["id"] for row in standby] == ["overflow"]
assert apply_mod.TARGET_ACTIVE == 60
assert apply_mod.TARGET_LANE == 20
shared=[
    {"id":"shared-fr","scope":"global","vf":True,"languages":["en","fr"],"types":["movie","tv"]},
    {"id":"global-only","scope":"global","vf":False,"languages":["en"],"types":["anime"]},
]
assert apply_mod.projects_to_vf(shared[0]) is True
assert apply_mod.projects_to_vf(shared[1]) is False
france_after=apply_mod.state_after_shared_global(
    {"active":59,"lanes":{"movie":19,"tv":18,"anime":21}},
    shared,
)
assert france_after=={"active":60,"lanes":{"movie":20,"tv":19,"anime":21}},france_after
selected_fr, standby_fr = apply_mod.select_to_target(
    [{"id":"france-only-extra","scope":"france","types":["movie","tv"]}],
    scope="france",
    current=france_after,
)
assert selected_fr==[] and [row["id"] for row in standby_fr]==["france-only-extra"]
assert apply_mod.defer_missing_probe_result(
    {"id":"slow","scope":"france","types":["movie","tv"]},
    "slow",
    set(),
)["routeDiscoveryLastReason"] == "probe_shard_missing_or_timeout"
assert apply_mod.defer_missing_probe_result(
    {"id":"already-active","scope":"global","types":["movie"]},
    "already-active",
    {"already-active"},
) is None

# Reserve intake is a non-active extension of the route-discovery pool; it must
# be deduplicated against the live batch rather than bypassing normal probing.
reserve_path=ROOT/"automation/provider-intake-reserve-contract-test.json"
try:
    reserve_path.write_text(json.dumps({
        "providers":[
            {"id":"reserve-new","scope":"global","direct":"https://reserve.example","types":["movie","tv","anime"]},
            {"id":"existing","scope":"global","direct":"https://duplicate.example","types":["movie"]},
        ]
    }),encoding="utf-8")
    rows=apply_mod.source_rows({
        "providers":[{"id":"existing","scope":"global","direct":"https://existing.example","types":["movie"]}],
        "deferredProviders":[],
    })
    by_id={row["id"]:row for row in rows}
    assert "reserve-new" in by_id
    assert by_id["existing"]["direct"] == "https://existing.example"
finally:
    reserve_path.unlink(missing_ok=True)

request={
    "providers":[{"id":"a","direct":"https://a.invalid"}],
    "deferredProviders":[{"id":"b","direct":"https://b.invalid"},{"id":"a","direct":"https://duplicate.invalid"}],
}
provider_ids=[row["id"] for row in probe.provider_rows(request)]
assert provider_ids[:2]==["a","b"], provider_ids
assert provider_ids.count("a")==1 and provider_ids.count("b")==1, provider_ids

workflow=(ROOT/".github/workflows/provider-bulk-route-discovery.yml").read_text(encoding="utf-8")
for token in (
    "matrix:",
    "--shard-count 16",
    "shard: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]",
    "tailscale/github-action@064b10558093f38325e838ddea35486bdc6b1d5c",
    'sudo tailscale set --exit-node="$TS_EXIT_NODE" --exit-node-allow-lan-access=false',
    "NIAKVIO_BULK_ROUTE_DISCOVERY_RESIDENTIAL=1",
    "actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9",
    "actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333",
    "source_version=evidence.get(\"requestVersion\")",
    "reason=no-qualified-routes",
    "actions: write",
    "gh workflow run provider-bulk-onboarding.yml --ref main",
    "FIELD_BULK_ROUTE_HANDOFF dispatched=provider-bulk-onboarding",
    "github.event_name == 'push' && github.sha || 'main'",
    "Partial route-discovery merge:",
    "--expected-shards 16",
):
    assert token in workflow, token

assert "provider-bulk-route-discovery.json" in workflow
assert "activation" not in probe_path.name.lower()
assert "id-token: write" in workflow
print("Bulk route-discovery sanitization, sharding, residential transport and explicit onboarding handoff contract passed")
