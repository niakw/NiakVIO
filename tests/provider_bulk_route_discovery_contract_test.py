#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str((ROOT/"scripts").resolve()))

probe_path=ROOT/"scripts/probe_bulk_provider_routes.py"
spec=importlib.util.spec_from_file_location("bulk_route_probe_test",probe_path)
probe=importlib.util.module_from_spec(spec); spec.loader.exec_module(probe)

fixture={"title":"Interstellar","tmdbId":"157336","mediaType":"movie"}
assert probe.route_pattern("/search?q=",fixture)=="/search?q={query}"
assert probe.route_pattern("/api?m=search&q=",fixture)=="/api?m=search&q={query}"
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
assert probe.identity_route_candidate("/search") is True
assert probe.identity_route_candidate("/movie/{tmdbId}") is True

request={
    "providers":[{"id":"a","direct":"https://a.invalid"}],
    "deferredProviders":[{"id":"b","direct":"https://b.invalid"},{"id":"a","direct":"https://duplicate.invalid"}],
}
assert [row["id"] for row in probe.provider_rows(request)]==["a","b"]

workflow=(ROOT/".github/workflows/provider-bulk-route-discovery.yml").read_text(encoding="utf-8")
for token in (
    "matrix:",
    "shard: [0, 1, 2, 3, 4, 5, 6, 7]",
    "tailscale/github-action@064b10558093f38325e838ddea35486bdc6b1d5c",
    'sudo tailscale set --exit-node="$TS_EXIT_NODE" --exit-node-allow-lan-access=false',
    "NIAKVIO_BULK_ROUTE_DISCOVERY_RESIDENTIAL=1",
    "actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9",
    "actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333",
    "source_version=evidence.get(\"requestVersion\")",
    "reason=no-qualified-routes",
):
    assert token in workflow, token

assert "provider-bulk-route-discovery.json" in workflow
assert "activation" not in probe_path.name.lower()
print("Bulk route-discovery sanitization, sharding and residential transport contract passed")
