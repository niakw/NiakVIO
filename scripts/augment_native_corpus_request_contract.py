#!/usr/bin/env python3
"""Augment generated native-corpus tests with the real Nuvio media-type contract.

The manifest vocabulary is strictly movie|tv|anime. Catalogue/user aliases are a
client input concern. The lab still traverses every staged provider (including
manifest-disabled rows), but executes only routes the provider declares compatible.
Anime fixtures deliberately exercise both anime and tv when a provider declares both,
because Nuvio catalogues may surface episodic anime through either route.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / ".github/triggers/nuvio-client-lab.json"
CANONICAL = {"movie", "tv", "anime"}
ALIASES = {"series": "tv", "show": "tv", "other": "tv"}


def canonical_type(value: object) -> str:
    raw = str(value or "").strip().lower()
    raw = ALIASES.get(raw, raw)
    if raw not in CANONICAL:
        raise SystemExit(f"unsupported native corpus media type: {raw!r}")
    return raw


def fixture(slug: str) -> dict:
    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    for row in data.get("fixtures", []):
        if isinstance(row, dict) and str(row.get("slug") or "") == slug and isinstance(row.get("fixture"), dict):
            return row["fixture"]
    raise SystemExit(f"unknown native corpus fixture: {slug}")


def manifest_types(path: Path) -> dict[str, list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, list[str]] = {}
    seen: set[str] = set()
    for row in data.get("scrapers", []):
        if not isinstance(row, dict):
            continue
        provider_id = str(row.get("id") or "").strip()
        if not provider_id:
            continue
        key = provider_id.casefold()
        if key in seen:
            raise SystemExit(f"duplicate provider id in canonical manifest: {provider_id}")
        seen.add(key)
        raw_types = row.get("supportedTypes")
        if not isinstance(raw_types, list) or not raw_types:
            raise SystemExit(
                f"provider {provider_id}: supportedTypes must be a non-empty list of canonical types"
            )
        types: list[str] = []
        for raw in raw_types:
            typ = str(raw or "").strip().lower()
            if typ not in CANONICAL:
                raise SystemExit(f"provider {provider_id}: non-canonical supportedType {typ!r}")
            if typ not in types:
                types.append(typ)
        out[key] = types
    if not out:
        raise SystemExit(f"manifest contains no providers: {path}")
    return out


def kotlin_map(values: dict[str, list[str]]) -> str:
    rows = []
    for provider_id, types in values.items():
        items = ", ".join(json.dumps(value) for value in types)
        rows.append(f"        {json.dumps(provider_id)} to setOf({items})")
    return "mapOf(\n" + ",\n".join(rows) + "\n    )"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"request-contract anchor {label!r} count={count}")
    return text.replace(old, new, 1)


def augment(path: Path, client: str, slug: str, manifest: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "FIELD_NATIVE_PROVIDER_SKIPPED" in text:
        print(f"FIELD_NATIVE_REQUEST_CONTRACT already=true client={client} fixture={slug} path={path}")
        return

    f = fixture(slug)
    fixture_media_type = canonical_type(f.get("mediaType") or "movie")
    fixture_category = str(f.get("category") or fixture_media_type).strip().lower()
    is_anime = fixture_category == "anime" or fixture_media_type == "anime"
    types = manifest_types(manifest)

    provider_list = re.search(r"(    private val providers = listOf\(\n.*?\n    \)\n)", text, flags=re.S)
    if not provider_list:
        raise SystemExit("request-contract provider list anchor missing")
    helpers = f'''\n    private val declaredTypesByProvider = {kotlin_map(types)}\n\n    private fun requestTypesFor(providerId: String, fixtureMediaType: String): List<String> {{\n        val declared = declaredTypesByProvider[providerId.lowercase()].orEmpty()\n        return if ({str(is_anime).lower()}) {{\n            listOf("anime", "tv").filter {{ it in declared }}\n        }} else {{\n            listOf(fixtureMediaType).filter {{ it in declared }}\n        }}\n    }}\n'''
    text = text[: provider_list.end()] + helpers + text[provider_list.end() :]

    if client in {"tv", "mobile"}:
        test_anchor = "    @Test\n"
        launch_helper = f'''    private fun launchClientUi() {{\n        val instrumentation = InstrumentationRegistry.getInstrumentation()\n        val context = instrumentation.targetContext\n        val packageName = context.packageName\n        val intent = context.packageManager.getLaunchIntentForPackage(packageName)\n        if (intent == null) {{\n            emit("FIELD_NATIVE_UI_LAUNCH_ERROR client={client} package64=${{b64(packageName)}} reason=no_launch_intent")\n            return\n        }}\n        intent.addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK or android.content.Intent.FLAG_ACTIVITY_CLEAR_TOP)\n        context.startActivity(intent)\n        Thread.sleep(1200L)\n        emit("FIELD_NATIVE_UI_LAUNCHED client={client} package64=${{b64(packageName)}}")\n    }}\n\n'''
        text = replace_once(text, test_anchor, launch_helper + test_anchor, "android test")
        begin = f'        emit("FIELD_NATIVE_CORPUS_BEGIN client={client} fixture=$fixtureSlug title64=${{b64(title)}} providers=${{providers.size}}")'
        text = replace_once(text, begin, f"        launchClientUi()\n{begin}", "ui launch")

    loop = "        for (provider in providers) {\n            val started = System.currentTimeMillis()\n            try {"
    replacement = f'''        for (provider in providers) {{\n            val requestTypes = requestTypesFor(provider.id, mediaType)\n            if (requestTypes.isEmpty()) {{\n                emit("FIELD_NATIVE_PROVIDER_SKIPPED client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} enabled=${{provider.enabled}} requested_type=$mediaType declared_types64=${{b64(declaredTypesByProvider[provider.id.lowercase()].orEmpty().sorted().joinToString(","))}} reason=unsupported_type")\n                continue\n            }}\n            for (requestMediaType in requestTypes) {{\n                val started = System.currentTimeMillis()\n                emit("FIELD_NATIVE_PROVIDER_BEGIN client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} enabled=${{provider.enabled}} request_type=$requestMediaType declared_types64=${{b64(declaredTypesByProvider[provider.id.lowercase()].orEmpty().sorted().joinToString(","))}}")\n                try {{'''
    text = replace_once(text, loop, replacement, "provider loop")
    text = replace_once(text, "                    mediaType = mediaType,", "                    mediaType = requestMediaType,", "runtime media type")

    markers = [
        "FIELD_NATIVE_RESULT",
        "FIELD_NATIVE_ROW",
        "FIELD_NATIVE_TRANSPORT",
        "FIELD_NATIVE_PLAYER",
        "FIELD_NATIVE_ERROR",
    ]
    for marker in markers:
        needle = f"{marker} client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}}"
        if needle in text:
            text = text.replace(needle, needle + " request_type=$requestMediaType")

    # Reader codegen runs after the base generator and therefore sees the nested
    # requestMediaType variable. Emit a visual phase marker before each real reader.
    reader_needle = "                    val reader = probeNativePlayer(row.url, row.headers,"
    if reader_needle in text:
        text = text.replace(
            reader_needle,
            f'                    emit("FIELD_NATIVE_PLAYER_BEGIN client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} request_type=$requestMediaType index=$index")\n' + reader_needle,
        )

    end_anchor = '        }\n        emit("FIELD_NATIVE_CORPUS_END client=' + client
    text = replace_once(text, end_anchor, '            }\n        }\n        emit("FIELD_NATIVE_CORPUS_END client=' + client, "nested request loop close")

    path.write_text(text, encoding="utf-8")
    print(
        f"FIELD_NATIVE_REQUEST_CONTRACT client={client} fixture={slug} media_type={fixture_media_type} "
        f"anime_dual_route={str(is_anime).lower()} providers={len(types)} path={path}"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("client", choices=("tv", "mobile", "desktop"))
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    manifest = Path(args.manifest)
    if not manifest.is_absolute():
        manifest = (ROOT / manifest).resolve()
    augment(Path(args.source).resolve(), args.client, args.fixture, manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
