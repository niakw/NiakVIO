#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "update_provider_device_results.py"

spec = importlib.util.spec_from_file_location("provider_device_results", MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

module.active_providers = lambda: [
    {
        "id": "demo",
        "key": "demo",
        "name": "Demo",
        "logo": "",
        "types": ["movie"],
    }
]

results = {
    "updatedAt": "2026-08-27",
    "fixtures": {
        "demo-movie": {
            "label": "Demo Movie",
            "mediaType": "movie",
        }
    },
    "proofs": [
        {
            "provider": "demo",
            "fixture": "demo-movie",
            "mediaType": "movie",
            "devices": {
                "tv": {
                    "verifiedAt": "2026-08-27",
                    "runId": "123",
                    "source": "official-native-reader",
                }
            },
        }
    ],
}

rendered = module.render(results)

for label in ("TV", "Mobile", "Desktop macOS", "Desktop Windows"):
    assert f"**{label}**" in rendered, label

assert "| 📺 **TV** | **1** | **1** | `2026-08-27` | ✅ Couvert par une preuve native |" in rendered
assert "| 📱 **Mobile** | **0** | **0** | `—` | 🟡 Suivi actif · aucune preuve positive conservée |" in rendered
assert "| 🖥️ **Desktop macOS** | **0** | **0** | `—` | 🟡 Suivi actif · aucune preuve positive conservée |" in rendered
assert "| 🪟 **Desktop Windows** | **0** | **0** | `—` | 🟡 Suivi actif · aucune preuve positive conservée |" in rendered
assert "📺 **TV** ✅" in rendered
assert "📱 **Mobile** ✅" not in rendered
assert "fixtures de test" in rendered
assert "TESTING_NOTICE.md" in rendered
assert "DISCLAIMER.md" in rendered
assert "Fixtures de test réellement validées" in rendered

print("provider device README coverage test passed")
