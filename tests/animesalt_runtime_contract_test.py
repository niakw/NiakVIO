#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
hubs=json.loads((ROOT/"provider-hubs.json").read_text(encoding="utf-8"))["providers"]["animesalt"]
overrides=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]["animesalt"]
assert hubs["direct"]=="https://animesalt.cx/"
assert hubs["direct_authority"]=="explicit_current"
assert "animesalt.cx" in hubs["allowed_terminal_hosts"]
assert "animesalt.link" in hubs.get("blocked_hosts",[])
assert overrides["official_site"]=="https://animesalt.cx"
src=(ROOT/"scripts/provider_patches/animesalt_runtime_v1.py").read_text(encoding="utf-8")
assert "NIAKVIO_ANIMESALT_RUNTIME_V1" in src
assert 'function runtimeBase()' in src
assert 'm&&(m.officialSite||m.knownSite)||c.base' in src
assert 'action=action_tr_search_suggest' in src
assert 'runtimeBase()+"/wp-admin/admin-ajax.php"' in src
assert '"&term="+encodeURIComponent(m.title)' in src
assert 'runtimeBase()+"/?s="+encodeURIComponent(m.title)' in src
assert '/player/index\\.php\\?data=' in src
assert 'data.videoSource||data.securedLink||data.file||data.url' in src
assert 'action=action_select_season&season=' in src
assert '"&post="+encodeURIComponent(chosen.post)' in src
assert '/player/index.php?data=' in src
assert '"hash="+encodeURIComponent(hash)+"&r="+encodeURIComponent(runtimeBase()+"/")' in src
assert 'data.videoSource||data.securedLink' in src
assert 'semanticLanes": ["anime"]' in src
js = src.split("WRAPPER = r'''",1)[1].split("'''",1)[0]
assert js.count("c.base") == 2, "only runtimeBase fallback may reference legacy cfg base"
print("AnimeSalt runtime contract passed")
