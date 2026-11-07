#!/usr/bin/env python3
"""Exact representative FORCE preference at the Deep process boundary.

Provider-local mutations and media validation remain owned by Deep Repair.
"""
from __future__ import annotations

import re
from typing import MutableMapping


def consume(argv: list[str], environ: MutableMapping[str, str]) -> tuple[list[str], str]:
    flag = "--force-preferred-profile"
    count = argv.count(flag)
    if count == 0:
        return list(argv), ""
    if count != 1:
        raise ValueError("duplicate Deep FORCE preferred profile")
    i = argv.index(flag)
    if i + 1 >= len(argv):
        raise ValueError("missing Deep FORCE preferred profile")
    profile = str(argv[i + 1]).strip().casefold()
    if not re.fullmatch(r"[a-z][a-z0-9_]*_v[0-9]+", profile):
        raise ValueError("invalid Deep FORCE preferred profile")
    if environ.get("NUVIO_BRAIN_EXPLORATION_CHAIN") != "1":
        raise ValueError("Deep FORCE preference requires exploratory chain")
    if str(environ.get("NUVIO_BRAIN_PLANNER_MODE") or "").casefold() == "learning":
        raise ValueError("Deep FORCE preference cannot target Learning mode")
    inherited = str(environ.get("NUVIO_BRAIN_FORCE_PREFERRED_PROFILE") or "").strip().casefold()
    if inherited and inherited != profile:
        raise ValueError("Deep FORCE preferred profile conflicts with caller")
    environ["NUVIO_BRAIN_FORCE_PREFERRED_PROFILE"] = profile
    return [*argv[:i], *argv[i + 2:]], profile
