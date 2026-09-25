#!/usr/bin/env python3
import json
from pathlib import Path
from scripts.badge_versioning import latest_catalog, latest_mapping

ROOT=Path(__file__).resolve().parents[1]
catalog_version,catalog_path=latest_catalog(ROOT)
mapping_version,mapping_path=latest_mapping(ROOT)
assert catalog_version>=5
assert mapping_version==catalog_version
for rel in (
    "assets/badge_catalog_v2_complete.json",
    "assets/badge_catalog_v4_complete.json",
    "assets/mapping_core_brain_ui_v2_complete.json",
    "assets/mapping_core_brain_ui_v4_complete.json",
):
    assert (ROOT/rel).is_file(), rel
catalog=json.loads(catalog_path.read_text(encoding="utf-8"))
mapping=json.loads(mapping_path.read_text(encoding="utf-8"))
assert catalog["publicFeedVersion"]==catalog_version
assert mapping["display"]["publicFeedVersion"]==catalog_version
assert len(catalog.get("badges") or [])>=309
assert any(g.get("id")=="stream-score" for g in catalog.get("groups") or [])
expected={"stream-score-s-plus","stream-score-s","stream-score-a-plus","stream-score-a","stream-score-b","stream-score-c","stream-score-d","stream-score-e"}
assert expected<={b.get("id") for b in catalog.get("badges") or []}
