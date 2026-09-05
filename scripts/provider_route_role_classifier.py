#!/usr/bin/env python3
"""NiakVIO-owned route role classifier extensions.

Keeps route semantics independent from any provider repository. The classifier is
conservative and only promotes route shapes with strong lexical evidence.
"""
from __future__ import annotations

import re
from typing import Any

VIDEO_PLAYER_RE = re.compile(r"/(?:video[-_]?player|watchplayer|iframeplayer)(?:[./?#-]|$)", re.I)
DOWNLOAD_SOURCE_RE = re.compile(r"/(?:download|file|mediafile)(?:[./?#-]|$)", re.I)
EPISODE_INDEX_RE = re.compile(r"/(?:episodes?(?:\.js|\.json|\.txt)?|season-list|episode-list)(?:[/?#.-]|$)", re.I)


def install(recognizer: Any) -> None:
    if getattr(recognizer, "_NIAKVIO_ROUTE_ROLE_CLASSIFIER_INSTALLED", False):
        return
    old = recognizer.route_kind

    def route_kind(route: str) -> str:
        value = str(route or "")
        if VIDEO_PLAYER_RE.search(value):
            return "player"
        if DOWNLOAD_SOURCE_RE.search(value):
            return "source"
        if EPISODE_INDEX_RE.search(value) and not re.search(r"/[^{]*\{(?:id|slug|query)\}", value, re.I):
            return "episode-index"
        return old(value)

    recognizer.route_kind = route_kind
    recognizer._NIAKVIO_ROUTE_ROLE_CLASSIFIER_INSTALLED = True
