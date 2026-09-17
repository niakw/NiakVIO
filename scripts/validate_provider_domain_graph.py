#!/usr/bin/env python3
"""Validate provider domain-routing metadata as one directed graph.

The three historical/runtime domain maps are authored independently but may
combine into a cycle after successive domain migrations.  This guard treats
host-like origin mappings as one graph and fails closed when:

* the current ``official_site`` host has an outgoing edge to another host; or
* distinct host edges across any combination of the maps form a cycle.

Non-domain textual/path replacements are intentionally ignored here; they are
validated by the normal override pipeline.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

DOMAIN_FIELDS = (
    "domain_substitutions",
    "replacements",
    "runtime_domain_replacements",
)


def _hostish(value: object, *, replacement: bool = False) -> str:
    raw = str(value or "").strip()
    if not raw or any(ch.isspace() for ch in raw):
        return ""

    has_scheme = "://" in raw
    candidate = raw if has_scheme else "https://" + raw
    try:
        parsed = urlsplit(candidate)
    except ValueError:
        return ""
    host = (parsed.hostname or "").strip(".").casefold()
    if not host or "." not in host:
        return ""

    # ``replacements`` can contain arbitrary strings/URLs.  Only origin-like
    # entries participate in domain authority.  The dedicated domain maps are
    # allowed to use either bare hosts or origin URLs.
    if replacement:
        if not has_scheme and ("/" in raw or "?" in raw or "#" in raw):
            return ""
        if has_scheme and (parsed.path not in ("", "/") or parsed.query or parsed.fragment):
            return ""
    elif has_scheme and (parsed.query or parsed.fragment):
        return ""
    return host


def _edges(patch: dict[str, Any]) -> list[tuple[str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    for field in DOMAIN_FIELDS:
        mapping = patch.get(field)
        if not isinstance(mapping, dict):
            continue
        for source, target in mapping.items():
            sh = _hostish(source, replacement=field == "replacements")
            th = _hostish(target, replacement=field == "replacements")
            if not sh or not th or sh == th:
                continue
            rows.append((sh, th, field, str(source), str(target)))
    return rows


def validate_patch(provider_id: str, patch: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    official_host = _hostish(patch.get("official_site"))
    edges = _edges(patch)

    for source, target, field, raw_source, raw_target in edges:
        if official_host and source == official_host:
            errors.append(
                f"{provider_id}: canonical host {official_host} has outgoing domain edge "
                f"in {field}: {raw_source!r} -> {raw_target!r}"
            )

    graph: dict[str, set[str]] = {}
    labels: dict[tuple[str, str], list[str]] = {}
    for source, target, field, raw_source, raw_target in edges:
        graph.setdefault(source, set()).add(target)
        labels.setdefault((source, target), []).append(
            f"{field}:{raw_source!r}->{raw_target!r}"
        )

    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> None:
        state[node] = 1
        stack.append(node)
        for target in sorted(graph.get(node, ())):
            if state.get(target) == 1:
                try:
                    start = stack.index(target)
                except ValueError:
                    start = 0
                cycle = stack[start:] + [target]
                evidence: list[str] = []
                for left, right in zip(cycle, cycle[1:]):
                    evidence.extend(labels.get((left, right), []))
                errors.append(
                    f"{provider_id}: combined domain cycle: {' -> '.join(cycle)}"
                    + (f" [{'; '.join(evidence)}]" if evidence else "")
                )
                continue
            if state.get(target) != 2:
                visit(target)
        stack.pop()
        state[node] = 2

    for node in sorted(graph):
        if state.get(node) is None:
            visit(node)
    return errors


def validate_patches(patches: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for provider_id, patch in sorted(patches.items()):
        if isinstance(patch, dict):
            errors.extend(validate_patch(str(provider_id), patch))
    return errors


def validate_document(document: dict[str, Any]) -> list[str]:
    patches = document.get("provider_patches") or {}
    if not isinstance(patches, dict):
        return ["provider_patches must be an object"]
    return validate_patches(patches)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="provider-overrides.json")
    args = parser.parse_args()
    path = Path(args.path)
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise SystemExit(f"{path}: JSON object required")
    errors = validate_document(document)
    if errors:
        raise SystemExit("provider domain graph validation failed:\n- " + "\n- ".join(errors))
    print("PROVIDER_DOMAIN_GRAPH_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
