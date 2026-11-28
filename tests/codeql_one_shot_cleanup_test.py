#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"scripts/delete_stale_codeql_one_shot_configurations.py"
spec=importlib.util.spec_from_file_location("cleanup",SOURCE)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

sha="a"*40
current_key=mod.MAINTAINED_KEY
stale_key=mod.STALE_ONE_SHOT_KEY

def analysis(category, *, key=current_key, commit=sha, analysis_id=1, deletable=False):
    return {
        "id":analysis_id,
        "commit_sha":commit,
        "analysis_key":key,
        "category":category,
        "deletable":deletable,
        "tool":{"name":"CodeQL"},
    }

maintained=[
    analysis("/language:actions"),
    analysis("/language:python"),
    analysis("/language:javascript-typescript/scope:core"),
    analysis("/language:javascript-typescript/scope:active-providers"),
    analysis("/language:javascript-typescript/scope:provider-bases"),
]
assert mod.replacement_complete(maintained,sha)
for index in range(len(maintained)):
    assert not mod.replacement_complete(maintained[:index]+maintained[index+1:],sha)
assert not mod.replacement_complete(
    maintained+[analysis("/language:javascript-typescript/scope:active-providers",commit="b"*40)],
    "b"*40,
)

rows=[
    analysis("/language:javascript-typescript/one-shot/shard:providers-0-f",
             key=stale_key,analysis_id=10,deletable=True),
    analysis("/language:javascript-typescript/one-shot/shard:provider-bases-g-l",
             key=stale_key,analysis_id=11,deletable=True),
    analysis("/language:javascript-typescript/scope:active-providers",
             key=current_key,analysis_id=12,deletable=True),
    analysis("/language:javascript-typescript/other",
             key=stale_key,analysis_id=13,deletable=True),
]
stale=mod.stale_one_shot_categories(rows)
assert set(stale)=={
    "/language:javascript-typescript/one-shot/shard:providers-0-f",
    "/language:javascript-typescript/one-shot/shard:provider-bases-g-l",
}
assert all(len(value)==1 for value in stale.values())

alerts=[
    {
        "number":1,
        "tool":{"name":"CodeQL"},
        "most_recent_instance":{
            "analysis_key":current_key,
            "commit_sha":sha,
            "category":"/language:javascript-typescript/scope:core",
        },
    },
    {
        "number":2,
        "tool":{"name":"CodeQL"},
        "most_recent_instance":{
            "analysis_key":current_key,
            "commit_sha":"b"*40,
            "category":"/language:javascript-typescript/scope:active-providers",
        },
    },
    {
        "number":3,
        "tool":{"name":"CodeQL"},
        "most_recent_instance":{
            "analysis_key":stale_key,
            "commit_sha":sha,
            "category":"/language:javascript-typescript/one-shot/shard:providers-0-f",
        },
    },
]
original=mod.guard.read_pages
try:
    mod.guard.read_pages=lambda *args,**kwargs: alerts
    current=mod.current_maintained_open_alerts(sha)
    assert [row["number"] for row in current]==[1]
    remaining=mod.remaining_stale_alerts()
    assert [row["number"] for row in remaining]==[3]
finally:
    mod.guard.read_pages=original

print("CodeQL one-shot cleanup contract passed")
