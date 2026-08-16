#!/usr/bin/env python3
"""Bounded public-search fallback for unresolved provider address discovery.

This complements resolve_provider_hubs.py without replacing it. It is attempted
only after curated hubs/direct candidates/LKG failed. It may discover a public
Telegram channel through Yandex/DuckDuckGo, then prefers the newest relevant
message id and validates the announced terminal before any routing state changes.
No spreadsheet/private prompt text is persisted.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import resolve_provider_hubs as hub  # noqa: E402


def _load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _brand_hint(provider_id: str, cfg: dict[str, Any], url: str, label: str) -> bool:
    text = hub.compact(f"{url} {label}")
    aliases = hub.aliases_for(provider_id, cfg)
    return any(alias and alias in text for alias in aliases)


def _terminal_candidates_from_search(provider_id: str, cfg: dict[str, Any], query: str, timeout: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    found: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    for engine, search_url in hub.search_engine_urls(query):
        try:
            status, final, document, _headers = hub.fetch(search_url, timeout)
        except Exception as exc:
            observations.append({"engine": engine, "status": 0, "error": type(exc).__name__})
            continue
        challenged = any(marker in document[:200_000].casefold() for marker in hub.SEARCH_CHALLENGE_MARKERS)
        observations.append({"engine": engine, "status": status, "challenged": challenged})
        if not 200 <= int(status) < 400 or challenged:
            continue
        for result_url, label, index in hub.links(document, final)[:24]:
            result_host = hub.host(result_url)
            if not result_host or result_host.endswith(hub.SEARCH_HOST_SUFFIXES + hub.INFRASTRUCTURE_HOST_SUFFIXES):
                continue
            if result_host.endswith(("t.me", "telegram.me", "telegram.org")):
                if not _brand_hint(provider_id, cfg, result_url, label):
                    continue
                try:
                    tg_status, tg_final, tg_document, _tg_headers = hub.fetch(result_url, timeout)
                except Exception:
                    continue
                if not 200 <= int(tg_status) < 400:
                    continue
                tg_cfg = dict(cfg)
                tg_cfg["resolver"] = "latest_telegram_domain"
                rows, _preferred = hub.choose_official(provider_id, tg_cfg, tg_final, tg_document)
                for row in rows[:6]:
                    found.append({
                        **row,
                        "source_type": "search_telegram",
                        "source": engine,
                        "query_kind": "public_provider_address",
                        "search_rank": index,
                    })
                continue
            if hub.same_brand(provider_id, result_url, cfg):
                found.append({
                    "url": result_url.rstrip("/"),
                    "label": label or f"{engine} search result",
                    "score": 42 - min(index, 10),
                    "source_type": "search",
                    "source": engine,
                    "query_kind": "public_provider_address",
                    "search_rank": index,
                })
    unique: dict[str, dict[str, Any]] = {}
    for row in found:
        url = str(row.get("url") or "").rstrip("/")
        if not url or not hub.is_public_url(url):
            continue
        previous = unique.get(url)
        if previous is None or int(row.get("score") or 0) > int(previous.get("score") or 0):
            unique[url] = row
    return sorted(unique.values(), key=lambda row: (-int(row.get("message_id") or -1), -int(row.get("score") or 0), row["url"])), observations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--max-providers", type=int, default=12)
    args = parser.parse_args()

    report_path = args.report if args.report.is_absolute() else ROOT / args.report
    output_path = args.output if args.output.is_absolute() else ROOT / args.output
    prior = _load(report_path, {})
    config = _load(hub.CONFIG_PATH, {})
    registry = hub.merge_hub_registry(config)
    history = _load(hub.HISTORY_PATH, {"schema_version": 1, "providers": {}})
    history_rows = history.setdefault("providers", {})

    unresolved = []
    for provider_id, row in (prior.get("providers") or {}).items():
        if not isinstance(row, dict):
            continue
        if row.get("status") in {"validated", "site_validated"}:
            continue
        cfg = registry.get(hub.canonical_provider_id(provider_id))
        if isinstance(cfg, dict):
            unresolved.append((hub.canonical_provider_id(provider_id), cfg))
    unresolved = unresolved[: max(0, int(args.max_providers))]

    summary: dict[str, Any] = {
        "schema_version": 1,
        "mode": "quick_search_fallback",
        "providers_considered": len(unresolved),
        "applied": 0,
        "providers": {},
        "privacy": "public-provider-address-data-only; no private spreadsheet/prompt text persisted",
    }
    for provider_id, cfg in unresolved:
        configured = [str(q).strip() for q in cfg.get("search_queries") or [] if str(q).strip()]
        queries = configured[:1] or [f"{provider_id} nouvelle adresse officielle telegram"]
        provider_row: dict[str, Any] = {"status": "inconclusive", "queries_attempted": len(queries), "observations": []}
        selected = None
        for query in queries:
            candidates, observations = _terminal_candidates_from_search(provider_id, cfg, query, args.timeout)
            provider_row["observations"].extend(observations)
            for candidate in candidates[:8]:
                validation = hub.validate_terminal(provider_id, cfg, str(candidate["url"]), args.timeout)
                if validation.get("ok"):
                    selected = {**candidate, **validation}
                    break
            if selected:
                break
        if selected:
            terminal = str(selected.get("final_url") or selected.get("url") or "").rstrip("/")
            item = {
                "provider_id": provider_id,
                "status": "site_validated",
                "reason": "public_search_terminal_runtime_validated",
                "official_site": terminal,
                "selected_source_type": selected.get("source_type"),
                "selected_source": selected.get("source"),
                "validated_api": None,
            }
            if args.apply:
                history_row = history_rows.setdefault(provider_id, {})
                changes = hub.update_provider_patch(config, provider_id, cfg, terminal, None, history_row)
                hub.update_history_row(history_row, item)
                summary["applied"] += len(changes)
                provider_row["applied_changes"] = len(changes)
            provider_row["status"] = "validated"
            provider_row["source_type"] = selected.get("source_type")
            provider_row["latest_message_id_used"] = selected.get("message_id")
            provider_row["terminal_host"] = hub.host(terminal)
        summary["providers"][provider_id] = provider_row

    output_path.parent.mkdir(parents=True, exist_ok=True)
    hub.atomic_write_json(output_path, summary)
    if args.apply and summary["applied"]:
        hub.atomic_write_json(hub.CONFIG_PATH, config)
        history["updated_at"] = hub.now_iso()
        hub.atomic_write_json(hub.HISTORY_PATH, history)
    print(f"provider public-search fallback complete: considered={len(unresolved)} applied={summary['applied']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
