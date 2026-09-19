#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts" / "upgrade_provider_base_runtime_v11.py"
spec = importlib.util.spec_from_file_location("upgrade_provider_base_runtime_v11", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

text = (ROOT / "scripts" / "provider_base_store.py").read_text(encoding="utf-8")
module.validate_telegram_discovery_only(text)

assert 'host === "t.me" || host.endsWith(".t.me")' in text
assert 'host === "telegram.me" || host.endsWith(".telegram.me")' in text
assert 'host === "telegram.dog" || host.endsWith(".telegram.dog")' in text
assert 'provider_discovery_only_host' in text

print("provider Telegram discovery-only contract passed: DNS-boundary runtime guard")
