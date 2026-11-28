#!/usr/bin/env python3
"""Authoritative Brain architecture prose uses neutral Bloc terminology."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHORITATIVE = [
    ROOT / "MEMORY.md",
    ROOT / "BRAIN_REPAIR_ARCHITECTURE.md",
    ROOT / "BRAIN_REPAIR_ROADMAP.md",
    ROOT / "PROVIDER_FAMILY_ARCHITECTURE.md",
    ROOT / "docs" / "BRAIN_REPAIR_EXECUTION_ROADMAP.md",
]
for path in AUTHORITATIVE:
    text = path.read_text(encoding="utf-8")
    assert not re.search(r"\bLego(?:s)?\b", text, re.IGNORECASE), path
    assert "Bloc" in text or "bloc" in text, path

ADDITIONAL_PUBLIC = [
    ROOT / ".github" / "workflows" / "provider-fast-repair.yml",
    ROOT / "automation" / "provider-v3-architecture.json",
]
for path in ADDITIONAL_PUBLIC:
    text = path.read_text(encoding="utf-8")
    assert not re.search(r"\bLego(?:s)?\b", text, re.IGNORECASE), path

print("FIELD_BRAIN_PUBLIC_TERMINOLOGY neutral_bloc=true brand_term=false")
