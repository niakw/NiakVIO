#!/usr/bin/env python3
"""Run the Domain Refresh transaction guard with explicit current-domain reuse evidence.

The base guard remains fail-closed. This wrapper adds two narrow fresh-evidence
cases used by authoritative address hubs: an explicitly labelled Active/Online
or Available/Disponible domain may legitimately reuse a historical hostname.
Labels containing Offline/Inactive or Unavailable/Indisponible/Blocked never
qualify.

Before the transaction guard runs, the complete provider override domain graph is
validated as one directed graph. This prevents independently-authored migration
maps from combining into a redirect cycle or making the current canonical domain
an outgoing redirect source.
"""
from __future__ import annotations

import re
from typing import Any

import validate_domain_refresh_transaction as guard
from validate_provider_domain_graph import validate_document as validate_domain_graph

_BASE = guard.has_fresh_rollback_evidence
_NEGATIVE = re.compile(r"\b(?:offline|inactive|unavailable|indisponible|blocked|bloqu[eé]e?s?)\b", re.I)
_POSITIVE = re.compile(r"\b(?:active|online|available|disponible)\b", re.I)


def has_fresh_rollback_evidence(item: dict[str, Any], terminal: str) -> bool:
    if _BASE(item, terminal):
        return True
    candidate = guard.selected_candidate(item, terminal)
    label = str(candidate.get("label") or "").casefold()
    if _NEGATIVE.search(label):
        return False
    return bool(_POSITIVE.search(label))


def main() -> int:
    graph_errors = validate_domain_graph(guard.load("provider-overrides.json"))
    if graph_errors:
        raise AssertionError(
            "provider domain graph validation failed before Domain Refresh publication:\n- "
            + "\n- ".join(graph_errors)
        )
    guard.has_fresh_rollback_evidence = has_fresh_rollback_evidence
    return guard.main()


if __name__ == "__main__":
    raise SystemExit(main())
