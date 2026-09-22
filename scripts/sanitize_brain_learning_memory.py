#!/usr/bin/env python3
"""Sanitize persistent Brain Learning memory for read-only Repair priors.

Only validated learned skill metadata crosses from brain-learning/proposals into
Fast Repair. Proposals, provider patches, endpoints, native diagnostics and
publication authority are deliberately discarded.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

URLISH = re.compile(r"(?i)(?:https?://|\b(?:authorization|cookie|token|secret)\s*[:=])")


def load(path: Path) -> dict[str, Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise ValueError("Learning memory must be an object")
    return value


def clean_text(value: object, limit: int) -> str:
    text=" ".join(str(value or "").split())[:limit]
    if URLISH.search(text):
        raise ValueError("unsafe URL/credential-shaped text in learned skill memory")
    return text


def clean_list(value: object, limit: int, item_limit: int) -> list[str]:
    if not isinstance(value,list):
        return []
    out=[]
    for raw in value[:limit]:
        text=clean_text(raw,item_limit)
        if text and text not in out:
            out.append(text)
    return out


def sanitize_skill(raw: object) -> dict[str, Any] | None:
    if not isinstance(raw,dict) or raw.get("validated") is not True:
        return None
    skill_id=clean_text(raw.get("id"),160)
    failure=clean_text(raw.get("failureClass") or raw.get("failure_class"),96)
    profile=clean_text(raw.get("profile"),96)
    if not skill_id or not failure or not profile:
        return None
    maturity=str(raw.get("maturity") or "experimental")
    if maturity not in {"experimental","candidate","trusted"}:
        maturity="experimental"
    try:
        confidence=max(0.0,min(1.0,float(raw.get("confidence") or 0.0)))
    except (TypeError,ValueError):
        confidence=0.0
    return {
        "id":skill_id,
        "failureClass":failure,
        "profile":profile,
        "actions":clean_list(raw.get("actions"),12,240),
        "capabilities":clean_list(raw.get("capabilities"),24,64),
        "providers":[x.casefold().replace("_","-") for x in clean_list(raw.get("providers"),96,128)],
        "successCount":max(0,int(raw.get("successCount") or 0)),
        "failureCount":max(0,int(raw.get("failureCount") or 0)),
        "validated":True,
        "confidence":confidence,
        "maturity":maturity,
        # Learning memory may suggest hypotheses, never auto-apply them in Repair.
        "autoApply":False,
        "lastValidatedMode":clean_text(raw.get("lastValidatedMode"),32),
        "memoryRole":"sanitized-learning-hypothesis-prior",
    }


def sanitize(value: dict[str, Any]) -> dict[str, Any]:
    if value.get("publicationAllowed") is not False or value.get("productionWritesAllowed") is not False:
        raise ValueError("Learning memory is not explicitly read-only")
    raw_skills=value.get("learnedSkills")
    skills={}
    if isinstance(raw_skills,dict):
        for key,raw in list(raw_skills.items())[:400]:
            skill=sanitize_skill(raw)
            if not skill:
                continue
            safe_key=clean_text(key or skill["id"],192)
            if safe_key:
                skills[safe_key]=skill
    return {
        "schemaVersion":1,
        "sourceSchemaVersion":max(0,int(value.get("schemaVersion") or 0)),
        "generatedAt":clean_text(value.get("generatedAt"),64),
        "publicationAllowed":False,
        "productionWritesAllowed":False,
        "learnedSkills":skills,
        "learnedSkillCount":len(skills),
        "discardedFields":[
            "proposals","experimentMemory","learningQueue","nativeReaderRepairMemory",
            "historicalTraining","nativeFeedback",
        ],
        "policy":"hypothesis-prior-only; ordinary Repair policy and current-byte gates remain authoritative",
    }


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    payload=sanitize(load(args.input))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"FIELD_BRAIN_LEARNING_MEMORY_IMPORT skills={payload['learnedSkillCount']} source_schema={payload['sourceSchemaVersion']}")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
