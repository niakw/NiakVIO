#!/usr/bin/env python3
"""Lexical/order-aware guard for Provider v3 route expression analysis.

The base expression analyzer intentionally stays lightweight, but a single global
assignment environment is unsafe when several functions reuse local names such as
`endpoint`, `url` or `path`. This guard resolves each fetch argument against only
assignments that occur before that call, preventing a later function from
rewriting an earlier route. No JavaScript is executed.
"""
from __future__ import annotations

import re
from typing import Any

import provider_route_expression_analyzer as analyzer


def install() -> None:
    if getattr(analyzer, "_NIAKVIO_ROUTE_SCOPE_GUARD_INSTALLED", False):
        return

    def scoped_extract_expression_routes(
        text: str,
        recognizer: Any,
    ) -> tuple[list[str], dict[str, dict[str, Any]], list[str]]:
        augmented, decoded = analyzer._decoded_text(text)
        routes: list[str] = []
        evidence: dict[str, dict[str, Any]] = {}

        # Resolve each request with the assignments visible at that exact source
        # position. This fixes repeated local names across functions without
        # pretending to implement or execute a full JavaScript scope engine.
        for match in analyzer.FETCH_CALL_RE.finditer(augmented):
            expr, end = analyzer._first_call_arg(augmented, match.end() - 1)
            local_env = analyzer._assignment_env(
                augmented[: match.start()], recognizer.expression_placeholder
            )
            value = analyzer._eval_expr(expr, local_env, recognizer.expression_placeholder)
            route = analyzer._normalize_route(value, recognizer)
            if not route:
                continue
            if route not in routes:
                routes.append(route)
            evidence[route] = {
                "call": match.group(1),
                "expression": expr[:900],
                "position": match.start(),
                "end": end,
                "executedEvidence": True,
                "evidence": "fetch-expression-scoped",
                "confidence": 0.99 if expr.strip().startswith(("'", '"', "`")) else 0.97,
            }

        # Keep assignment-only and decoded evidence, but never let it overwrite
        # stronger request-site evidence produced above.
        env = analyzer._assignment_env(augmented, recognizer.expression_placeholder)
        for name, value in env.items():
            route = analyzer._normalize_route(value, recognizer)
            if not route or not recognizer.route_is_executable_candidate(route):
                continue
            if route not in routes:
                routes.append(route)
            evidence.setdefault(
                route,
                {
                    "call": None,
                    "expression": name,
                    "position": -1,
                    "end": -1,
                    "executedEvidence": bool(
                        re.search(
                            r"\b(?:fetch|fetchText|fetchJson|fetchPlain|request)\s*\(\s*"
                            + re.escape(name)
                            + r"\b",
                            augmented,
                            re.I,
                        )
                    ),
                    "evidence": "route-assignment",
                    "confidence": 0.90,
                },
            )

        for value in decoded:
            route = analyzer._normalize_route(value, recognizer)
            if not route or not recognizer.route_is_executable_candidate(route):
                continue
            if route not in routes:
                routes.append(route)
            evidence.setdefault(
                route,
                {
                    "call": None,
                    "expression": "decoded-static-string",
                    "position": -1,
                    "end": -1,
                    "executedEvidence": False,
                    "evidence": "decoded-static-string",
                    "confidence": 0.72,
                },
            )

        return routes[:192], evidence, decoded

    analyzer.extract_expression_routes = scoped_extract_expression_routes
    analyzer._NIAKVIO_ROUTE_SCOPE_GUARD_INSTALLED = True
