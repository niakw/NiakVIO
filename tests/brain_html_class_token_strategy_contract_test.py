#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
planner = (ROOT / "engine_v2/scripts/plan-repairs.mjs").read_text(encoding="utf-8")
runtime = (ROOT / "scripts/adaptive_runtime/runtime_repair.py").read_text(encoding="utf-8")

profile = "html_class_token_exact_v1"
assert profile in runtime
assert f'{{ profile: "{profile}", method: "exact-html-class-token-contract" }}' in planner
route = planner.index("route_proven_gap:")
search = planner.index("search_gap:")
assert planner.index(profile, route) < planner.index("route_transition_graph_v1", route)
assert planner.index(profile, search) < planner.index("search_contract_inference_v1", search)
assert '"scripts/adaptive_runtime/html_class_token_exact_v1.py"' in planner
print("Brain HTML class-token strategy contract passed")
