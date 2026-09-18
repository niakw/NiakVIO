#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
reg=json.loads((ROOT/"automation/provider-repair-survival-registry.json").read_text(encoding="utf-8"))
assert len(reg["providers"])>=15
assert reg["providers"]["sekai"]["requiredScripts"]==["scripts/provider_patches/sekai_nondisplay_runtime_v1.py","scripts/provider_patches/sekai_nondisplay_recovery_v2.py","scripts/provider_patches/sekai_inline_media_runtime_v1.py"]
assert "scripts/provider_patches/animesamaco_nondisplay_recovery_v2.py" in reg["providers"]["animesama-co"]["requiredScripts"]
assert "scripts/provider_patches/neko_sama_nondisplay_recovery_v2.py" in reg["providers"]["neko-sama"]["requiredScripts"]
assert "scripts/provider_patches/voiranime_rip_nondisplay_recovery_v2.py" in reg["providers"]["voiranime-rip"]["requiredScripts"]
assert "scripts/provider_patches/anikototv_runtime_v3.py" in reg["providers"]["anikototv"]["requiredScripts"]
assert reg["providers"]["allwish"]["requiredScripts"]==["scripts/provider_patches/allwish_current_runtime_v2.py"]
assert reg["providers"]["vidfast"]["requiredScripts"]==["scripts/provider_patches/vidfast_current_runtime_v2.py"]
assert reg["providers"]["vidlove"]["requiredScripts"]==["scripts/provider_patches/vidlove_current_api_v2.py"]
assert len(reg["providers"]["wookafr"]["requiredScripts"])==3
assert reg["rules"]["historicalProofDoesNotAutoCertify"] is True
print("provider repair survival registry tests passed")
