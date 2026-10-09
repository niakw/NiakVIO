#!/usr/bin/env python3
"""Brain FORCE typed recovery-program compiler.

The local 7B advisor chooses a causal combination of existing verified
cross-provider recovery primitives; Brain compiles it into a distinct Python
strategy branch. This is *not* a provider patch, a hard-coded candidate or
playback proof. Current-byte sandbox/replay decides whether it works.
"""
from __future__ import annotations

import ast
import json
from typing import Any

SEARCH = {
    "configured": "configured_search",
    "learned": "learned_search",
    "peer": "peer_search",
    "generic": "generic_search",
}
DIRECT = {
    "configured": "configured_direct",
    "learned": "learned_direct",
    "peer": "peer_direct",
    "positive": "positive_program_routes(provider_id)",
}
REQUESTS = {
    "current": "current_request_recipes",
    "positive": "positive_request_recipes",
    "historical": "historical_provider_request_recipes",
    "provider": "provider_request_recipes",
    "peer": "peer_request_recipes",
}
ROLES = {"source", "api", "player", "episode", "detail", "other"}


def _choices(data: Any, options: dict[str, str], label: str) -> tuple[list[str], list[str]]:
    if not isinstance(data, list) or not 1 <= len(data) <= 5:
        raise ValueError(f"architecture FORCE recoveryProgram invalid {label} sources")
    names = [str(x or "") for x in data]
    if len(set(names)) != len(names) or any(key not in options for key in names):
        raise ValueError(f"architecture FORCE recoveryProgram unsupported or duplicate {label} source")
    return names, [options[key] for key in names]


def _budget(data: dict[str, Any], key: str, upper: int) -> int:
    raw = data.get(key)
    if isinstance(raw, bool) or not isinstance(raw, int) or not 4 <= raw <= upper:
        raise ValueError(f"architecture FORCE recoveryProgram invalid {key} budget")
    return raw


def compile_recovery_program(program: dict[str, Any], *, max_chars: int = 4200) -> str:
    if not isinstance(program, dict):
        raise ValueError("architecture FORCE recoveryProgram must be a structured object")
    expected = {
        "searchSources", "directSources", "requestSources",
        "roleOrder", "transitionMode", "terminalRoleFilter", "budgets",
    }
    if set(program) != expected:
        raise ValueError("architecture FORCE recoveryProgram missing or unknown fields")
    search_names, search_parts = _choices(program["searchSources"], SEARCH, "search")
    direct_names, direct_parts = _choices(program["directSources"], DIRECT, "direct")
    request_names, request_parts = _choices(program["requestSources"], REQUESTS, "request")
    role_order = program["roleOrder"]
    if (
        not isinstance(role_order, list)
        or not 2 <= len(role_order) <= 6
        or len(set(role_order)) != len(role_order)
        or any(str(x) not in ROLES for x in role_order)
    ):
        raise ValueError("architecture FORCE recoveryProgram invalid role order")
    if type(program["terminalRoleFilter"]) is not bool:
        raise ValueError("architecture FORCE recoveryProgram invalid terminal filter")
    transition = program["transitionMode"]
    if transition not in {"none", "owned-direct", "owned-learned", "owned-combined"}:
        raise ValueError("architecture FORCE recoveryProgram invalid transition mode")
    budget = program["budgets"]
    if not isinstance(budget, dict) or set(budget) != {"search", "direct", "requests", "transitions"}:
        raise ValueError("architecture FORCE recoveryProgram invalid budgets")
    s_limit = _budget(budget, "search", 40)
    d_limit = _budget(budget, "direct", 72)
    r_limit = _budget(budget, "requests", 72)
    t_limit = _budget(budget, "transitions", 32)

    # Avoid accepting mere v2 relabels: at least one new evidence source or
    # distinct terminal-focused/transition mechanism is compulsory.
    new_evidence = bool(
        {"peer", "generic"}.intersection(search_names)
        or "peer" in direct_names
        or "peer" in request_names
        or program["terminalRoleFilter"] is True
        or transition in {"owned-learned", "owned-combined"}
    )
    if not new_evidence:
        raise ValueError("architecture FORCE recoveryProgram duplicates exhausted v2 mechanisms")

    if program["terminalRoleFilter"]:
        direct_parts = [
            f'[route for route in {src} if _route_role(route) in TERMINAL_MEDIA_ROLES | {{"episode"}}]'
            for src in direct_parts
        ]
    lines = [
        "search_paths = _unique_routes(" + ", ".join(search_parts) + f", limit={s_limit})",
        "direct_paths = _unique_routes(" + ", ".join(direct_parts) + f", limit={d_limit})",
        "request_recipes = _unique_request_recipes(" + ", ".join(request_parts) + f", limit={r_limit})",
    ]
    if transition == "owned-direct":
        lines.append(f"transition_prefixes = _owned_transition_prefixes(direct_paths, limit={t_limit})")
    elif transition == "owned-learned":
        lines.append(f"transition_prefixes = _owned_transition_prefixes(learned_direct, limit={t_limit})")
    elif transition == "owned-combined":
        lines.append(
            "transition_prefixes = _owned_transition_prefixes("
            f"_unique_routes(direct_paths, learned_direct, limit={max(d_limit,t_limit)}), limit={t_limit})"
        )
    lines.append("second_order_role_preferences = " + json.dumps(role_order))
    body = "\n".join(lines) + "\n"
    if len(body) > max_chars:
        raise ValueError("architecture FORCE recoveryProgram exceeds bounded executor")
    ast.parse("if True:\n" + "".join("    " + line + "\n" for line in lines))
    return body
