#!/usr/bin/env python3
"""Augment generated native-corpus tests with the real Nuvio media-type contract.

The manifest vocabulary is strictly movie|tv|anime. Catalogue/user aliases are a
client input concern. The lab still traverses every staged provider (including
manifest-disabled rows), but executes only meaningful media routes.

For episodic anime, Nuvio catalogues may surface the same title through a series/tv
route or an anime route. A provider that already declares either tv or anime is
therefore exercised on BOTH routes. The declared route is normal validation; the
other route is explicitly tagged ``capability_probe``. A failed capability probe is
never a provider failure or Brain repair signal. A successful end-to-end probe can
justify a later supportedTypes expansion.
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
        rows.append(
            f"        Pair<String, Set<String>>({json.dumps(provider_id)}, setOf<String>({items}))"
        )
    # NuvioTV's androidTest Kotlin compiler has failed to infer the generic T of
    # the infix `to` helper in this generated nested map. Keep the complete Pair
    # type explicit so TV and Mobile consume one deterministic request contract.
    return "mapOf<String, Set<String>>(\n" + ",\n".join(rows) + "\n    )"


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
    helpers = f'''\n    data class ProviderRequestRoute(val mediaType: String, val declared: Boolean)\n\n    private val declaredTypesByProvider: Map<String, Set<String>> = {kotlin_map(types)}\n\n    private fun requestRoutesFor(providerId: String, fixtureMediaType: String): List<ProviderRequestRoute> {{\n        val declared: Set<String> = declaredTypesByProvider[providerId.lowercase()] ?: emptySet<String>()\n        return if ({str(is_anime).lower()}) {{\n            // Episodic anime can enter Nuvio through either anime or series/tv.\n            // If a provider participates in either ecosystem, test both. The\n            // undeclared side is discovery evidence only and cannot fail the provider.\n            if ("anime" !in declared && "tv" !in declared) emptyList<ProviderRequestRoute>()\n            else listOf("anime", "tv").map {{ type: String -> ProviderRequestRoute(type, type in declared) }}\n        }} else {{\n            listOf<String>(fixtureMediaType).filter {{ it in declared }}\n                .map {{ type -> ProviderRequestRoute(type, true) }}\n        }}\n    }}\n'''
    text = text[: provider_list.end()] + helpers + text[provider_list.end() :]

    if client in {"tv", "mobile"}:
        test_anchor = "    @Test\n"
        if client == "mobile":
            # composeApp device tests run under a test package, while the real
            # official debug application is produced by androidApp and overrides
            # its applicationId to com.nuviodebug.com. Prefer that real launcher;
            # retain the instrumentation-derived package only as a compatibility
            # fallback for upstream changes.
            launch_helper = '''    private fun launchClientUi() {\n        val instrumentation = InstrumentationRegistry.getInstrumentation()\n        val context = instrumentation.targetContext\n        var packageName: String = "com.nuviodebug.com"\n        var intent: android.content.Intent? = context.packageManager.getLaunchIntentForPackage(packageName)\n        if (intent == null) {\n            val instrumentationPackage: String = context.packageName\n            packageName = if (instrumentationPackage.endsWith(".test")) instrumentationPackage.removeSuffix(".test") else instrumentationPackage\n            intent = context.packageManager.getLaunchIntentForPackage(packageName)\n        }\n        val launchIntent: android.content.Intent? = intent\n        if (launchIntent == null) {\n            emit("FIELD_NATIVE_UI_LAUNCH_ERROR client=mobile package64=${b64(packageName)} reason=no_launch_intent")\n            return\n        }\n        launchIntent.addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK or android.content.Intent.FLAG_ACTIVITY_CLEAR_TOP)\n        context.startActivity(launchIntent)\n        Thread.sleep(1200L)\n        emit("FIELD_NATIVE_UI_LAUNCHED client=mobile package64=${b64(packageName)}")\n    }\n\n'''
        else:
            launch_helper = '''    private fun launchClientUi() {\n        val instrumentation = InstrumentationRegistry.getInstrumentation()\n        val context = instrumentation.targetContext\n        val instrumentationPackage: String = context.packageName\n        val packageName: String = if (instrumentationPackage.endsWith(".test")) instrumentationPackage.removeSuffix(".test") else instrumentationPackage\n        val intent: android.content.Intent? = context.packageManager.getLaunchIntentForPackage(packageName)\n        if (intent == null) {\n            emit("FIELD_NATIVE_UI_LAUNCH_ERROR client=tv package64=${b64(packageName)} reason=no_launch_intent")\n            return\n        }\n        intent.addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK or android.content.Intent.FLAG_ACTIVITY_CLEAR_TOP)\n        context.startActivity(intent)\n        Thread.sleep(1200L)\n        emit("FIELD_NATIVE_UI_LAUNCHED client=tv package64=${b64(packageName)}")\n    }\n\n'''
        text = replace_once(text, test_anchor, launch_helper + test_anchor, "android test")
        begin = f'        emit("FIELD_NATIVE_CORPUS_BEGIN client={client} fixture=$fixtureSlug title64=${{b64(title)}} providers=${{providers.size}}")'
        text = replace_once(text, begin, f"        launchClientUi()\n{begin}", "ui launch")

    loop = "        for (provider in providers) {\n            val started = System.currentTimeMillis()\n            try {"
    replacement = f'''        for (provider in providers) {{\n            val requestRoutes = requestRoutesFor(provider.id, mediaType)\n            if (requestRoutes.isEmpty()) {{\n                emit("FIELD_NATIVE_PROVIDER_SKIPPED client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} enabled=${{provider.enabled}} requested_type=$mediaType declared_types64=${{b64(declaredTypesByProvider[provider.id.lowercase()].orEmpty().sorted().joinToString(","))}} reason=unsupported_type")\n                continue\n            }}\n            for (requestRoute in requestRoutes) {{\n                val requestMediaType = requestRoute.mediaType\n                val routeMode = if (requestRoute.declared) "declared" else "capability_probe"\n                val started = System.currentTimeMillis()\n                emit("FIELD_NATIVE_PROVIDER_BEGIN client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} enabled=${{provider.enabled}} request_type=$requestMediaType route_mode=$routeMode declared_types64=${{b64(declaredTypesByProvider[provider.id.lowercase()].orEmpty().sorted().joinToString(","))}}")\n                try {{'''
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
            text = text.replace(needle, needle + " request_type=$requestMediaType route_mode=$routeMode")

    reader_needle = "                    val reader = probeNativePlayer(row.url, row.headers,"
    if reader_needle in text:
        text = text.replace(
            reader_needle,
            f'                    emit("FIELD_NATIVE_PLAYER_BEGIN client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} request_type=$requestMediaType route_mode=$routeMode index=$index")\n' + reader_needle,
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
