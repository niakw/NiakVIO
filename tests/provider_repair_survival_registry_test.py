#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
reg=json.loads((ROOT/"automation/provider-repair-survival-registry.json").read_text(encoding="utf-8"))
assert len(reg["providers"])>=15
assert reg["providers"]["sekai"]["requiredScripts"]==["scripts/provider_patches/non_display_recovery_runtime_v1.py"]
assert "scripts/provider_patches/anikototv_runtime_v3.py" in reg["providers"]["anikototv"]["requiredScripts"]
assert len(reg["providers"]["wookafr"]["requiredScripts"])==3
assert reg["rules"]["historicalProofDoesNotAutoCertify"] is True
print("provider repair survival registry tests passed")
