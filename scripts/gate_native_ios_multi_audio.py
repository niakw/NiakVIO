#!/usr/bin/env python3
"""Fail closed when a proven multi-audio HLS master collapses in Nuvio iOS."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

MARKER = "FIELD_NATIVE_IOS_PLAYER "

LANGUAGE_ALIASES = {
    "eng": "en", "english": "en", "anglais": "en",
    "fra": "fr", "fre": "fr", "french": "fr", "francais": "fr", "français": "fr",
    "deu": "de", "ger": "de", "german": "de", "deutsch": "de",
    "spa": "es", "spanish": "es", "espanol": "es", "español": "es",
    "por": "pt", "portuguese": "pt", "portugues": "pt", "português": "pt",
    "ita": "it", "italian": "it", "italiano": "it",
    "jpn": "ja", "japanese": "ja", "japonais": "ja",
    "kor": "ko", "korean": "ko", "coreen": "ko", "coréen": "ko",
    "zho": "zh", "chi": "zh", "chinese": "zh", "chinois": "zh",
}


def normalize_languages(raw: object) -> list[str]:
    output: list[str] = []
    for value in str(raw or "").split(","):
        token = value.strip().casefold().replace("_", "-")
        if not token or token == "und":
            continue
        direct = LANGUAGE_ALIASES.get(token)
        if direct:
            normalized = direct
            if normalized not in output:
                output.append(normalized)
            continue
        first_word = token.split(" ", 1)[0].split("(", 1)[0]
        if first_word in LANGUAGE_ALIASES:
            normalized = LANGUAGE_ALIASES[first_word]
            if normalized not in output:
                output.append(normalized)
            continue
        parts = [part for part in token.split("-") if part]
        if not parts:
            continue
        parts[0] = LANGUAGE_ALIASES.get(parts[0], parts[0])
        normalized = "-".join(parts)
        if normalized not in output:
            output.append(normalized)
    return output


def language_equivalent(expected: str, observed: str) -> bool:
    return expected == observed or expected.split("-", 1)[0] == observed.split("-", 1)[0]


def language_coverage(expected: list[str], observed: list[str]) -> bool:
    used: set[int] = set()
    for language in expected:
        match = next(
            (
                index
                for index, candidate in enumerate(observed)
                if index not in used and language_equivalent(language, candidate)
            ),
            None,
        )
        if match is None:
            return False
        used.add(match)
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument(
        "--require-witness",
        action="store_true",
        help="Fail when the corpus contains no transport-proven multi-audio master.",
    )
    args = parser.parse_args()

    expected = 0
    verified = 0
    language_expected = 0
    language_verified = 0
    collapsed: list[str] = []
    language_collapsed: list[str] = []

    for raw in args.log.read_text(encoding="utf-8", errors="replace").splitlines():
        marker = raw.find(MARKER)
        if marker < 0:
            continue
        payload = raw[marker + len(MARKER):].strip()
        try:
            row = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue

        master_count = int(row.get("masterAudioTrackCount") or 0)
        if master_count < 2:
            continue
        expected += 1
        player_count = int(row.get("audioTrackCount") if row.get("audioTrackCount") is not None else -1)
        if player_count >= 2:
            verified += 1
        else:
            collapsed.append(
                f"{row.get('fixture') or 'unknown'}:{row.get('provider') or 'unknown'}:"
                f"master={master_count}:player={player_count}"
            )

        master_languages = normalize_languages(row.get("masterAudioTrackLanguages"))
        if len(master_languages) >= 2:
            language_expected += 1
            player_languages = normalize_languages(row.get("audioTrackLanguages"))
            if len(player_languages) >= 2 and language_coverage(master_languages, player_languages):
                language_verified += 1
            else:
                language_collapsed.append(
                    f"{row.get('fixture') or 'unknown'}:{row.get('provider') or 'unknown'}:"
                    f"master_lang={','.join(master_languages)}:"
                    f"player_lang={','.join(player_languages) or 'none'}"
                )

    if collapsed or language_collapsed:
        details = [*collapsed, *language_collapsed]
        print(
            "FIELD_NATIVE_IOS_MULTI_AUDIO_GATE "
            f"status=fail expected={expected} verified={verified} collapsed={len(collapsed)} "
            f"language_expected={language_expected} language_verified={language_verified} "
            f"language_collapsed={len(language_collapsed)} details={';'.join(details[:12])}"
        )
        return 2

    if args.require_witness and expected < 1:
        print(
            "FIELD_NATIVE_IOS_MULTI_AUDIO_GATE "
            "status=unproven expected=0 verified=0 collapsed=0 language_expected=0 "
            "language_verified=0 require_witness=true reason=no_multi_audio_witness"
        )
        return 3
    if args.require_witness and language_expected < 1:
        print(
            "FIELD_NATIVE_IOS_MULTI_AUDIO_GATE "
            f"status=unproven expected={expected} verified={verified} collapsed=0 "
            "language_expected=0 language_verified=0 require_witness=true "
            "reason=no_distinct_language_witness"
        )
        return 3

    print(
        "FIELD_NATIVE_IOS_MULTI_AUDIO_GATE "
        f"status=pass expected={expected} verified={verified} collapsed=0 "
        f"language_expected={language_expected} language_verified={language_verified} language_collapsed=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
