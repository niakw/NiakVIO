#!/usr/bin/env python3
from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import add_provider

rows = add_provider.request_sources(
    hub="",
    direct="",
    telegram="",
    api="",
    search_queries=[],
    structured_sources=[
        {
            "type": "hub",
            "url": "https://address.example/",
            "priority": 120,
            "role": "primary",
            "resolver": "service_catalogue",
            "official_link_labels": ["current site"],
        },
        {
            "type": "telegram_public",
            "url": "https://t.me/s/example",
            "priority": 100,
            "role": "fallback",
            "resolver": "telegram_description",
        },
        {
            "type": "redirect",
            "url": "https://go.example/",
            "priority": 90,
            "role": "fallback",
            "resolver": "redirect",
        },
    ],
)
assert len(rows) == 3, rows
assert rows[0]["resolver"] == "service_catalogue", rows
assert rows[1]["resolver"] == "telegram_description", rows
assert rows[1]["role"] == "fallback", rows
assert rows[2]["type"] == "redirect" and rows[2]["resolver"] == "redirect", rows

# Legacy fields remain accepted and do not duplicate equivalent structured rows.
legacy = add_provider.request_sources(
    hub="https://address.example/",
    direct="https://provider.example/",
    telegram="https://t.me/s/example",
    api="",
    search_queries=['"Example" official domain'],
    structured_sources=rows,
)
identities = [
    (str(row.get("type")), str(row.get("url") or row.get("query") or "").rstrip("/").casefold())
    for row in legacy
]
assert len(identities) == len(set(identities)), identities
assert any(row.get("type") == "search" and row.get("role") == "fallback" for row in legacy), legacy

# Discovery authority is metadata only. Onboarding may preserve officialHub,
# but it must never seed hub/Telegram hosts as executable provider origins or
# knownSite.
stage_source = inspect.getsource(add_provider.stage)
assert "for value in (direct, api):" in stage_source, stage_source
assert "for value in (direct, hub, telegram, api):" not in stage_source, stage_source
assert '"knownSite": direct or None' in stage_source, stage_source
assert "known_site=direct or None" in stage_source, stage_source
assert '"sources": address_sources' in stage_source, stage_source

try:
    add_provider.request_sources(
        hub="",
        direct="",
        telegram="",
        api="",
        search_queries=[],
        structured_sources=[{"type": "unsupported", "url": "https://bad.example/"}],
    )
except ValueError as exc:
    assert "unsupported provider hub source type" in str(exc), exc
else:
    raise AssertionError("unsupported discovery source type must fail closed")

print("provider onboarding multi-hub discovery contract passed")
