#!/usr/bin/env python3
"""Augment generated native-corpus tests with the real Nuvio media-type contract.

Canonical provider identity is strictly movie|tv|anime, while Nuvio transport
metadata may additionally expose aliases such as series. The lab still traverses every
staged provider (including manifest-disabled rows), but executes only canonical media routes.

Canonical native acceptance selects providers with the logical fixture media type.
Anime therefore remains anime for provider selection, while the Nuvio plugin ABI
receives its TV transport alias only after selection. Cross-type capability discovery
belongs to Learning/Deep, not to this acceptance layer.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
CORPUS = ROOT / ".github/triggers/nuvio-client-lab.json"
CANONICAL = {"movie", "tv", "anime"}
TRANSPORT = CANONICAL | {"series"}

from native_media_type_contract import canonical_media_type, fixture_media_type  # noqa: E402
from rotating_corpus import fixture_by_slug as rotating_fixture_by_slug  # noqa: E402


def canonical_type(value: object) -> str:
    try:
        return canonical_media_type(value)
    except ValueError as error:
        raise SystemExit(str(error)) from error


def fixture(slug: str) -> dict:
    try:
        row = rotating_fixture_by_slug(slug)
    except KeyError as error:
        raise SystemExit(str(error)) from error
    return {key: value for key, value in row.items() if key not in {"slug", "lane"}}


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
        raw_supported = row.get("supportedTypes")
        if not isinstance(raw_supported, list) or not raw_supported:
            raise SystemExit(
                f"provider {provider_id}: supportedTypes must be a non-empty transport list"
            )
        supported: list[str] = []
        for raw in raw_supported:
            typ = str(raw or "").strip().lower()
            if typ not in TRANSPORT:
                raise SystemExit(f"provider {provider_id}: invalid transport supportedType {typ!r}")
            if typ not in supported:
                supported.append(typ)

        raw_canonical = row.get("canonicalSupportedTypes")
        if isinstance(raw_canonical, list) and raw_canonical:
            canonical_source = raw_canonical
        else:
            canonical_source = [value for value in supported if value in CANONICAL]
        types: list[str] = []
        for raw in canonical_source:
            typ = str(raw or "").strip().lower()
            if typ not in CANONICAL:
                raise SystemExit(f"provider {provider_id}: non-canonical canonicalSupportedType {typ!r}")
            if typ not in types:
                types.append(typ)
        if not types:
            raise SystemExit(f"provider {provider_id}: canonicalSupportedTypes must not be empty")
        out[key] = types
    if not out:
        raise SystemExit(f"manifest contains no providers: {path}")
    return out


def manifest_transport_types(path: Path) -> dict[str, list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, list[str]] = {}
    for row in data.get("scrapers", []):
        if not isinstance(row, dict):
            continue
        provider_id = str(row.get("id") or "").strip()
        if not provider_id:
            continue
        raw_supported = row.get("supportedTypes")
        if not isinstance(raw_supported, list) or not raw_supported:
            raise SystemExit(f"provider {provider_id}: supportedTypes must be a non-empty transport list")
        values: list[str] = []
        for raw in raw_supported:
            typ = str(raw or "").strip().lower()
            if typ not in TRANSPORT:
                raise SystemExit(f"provider {provider_id}: invalid transport supportedType {typ!r}")
            if typ not in values:
                values.append(typ)
        out[provider_id.casefold()] = values
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
    resolved_fixture_media_type = fixture_media_type(f)
    types = manifest_types(manifest)
    transport_types = manifest_transport_types(manifest)

    provider_list = re.search(r"(    private val providers = listOf\(\n.*?\n    \)\n)", text, flags=re.S)
    if not provider_list:
        raise SystemExit("request-contract provider list anchor missing")
    helpers = f'''\n    data class ProviderRequestRoute(val mediaType: String)\n\n    private val declaredTypesByProvider: Map<String, Set<String>> = {kotlin_map(types)}\n\n    private val transportTypesByProvider: Map<String, Set<String>> = {kotlin_map(transport_types)}\n\n    private val logicalFixtureMediaType: String = {json.dumps(resolved_fixture_media_type)}\n\n    private fun requestRoutesFor(providerId: String, fixtureMediaType: String): List<ProviderRequestRoute> {{\n        val declared: Set<String> = declaredTypesByProvider[providerId.lowercase()] ?: emptySet<String>()\n        if (logicalFixtureMediaType !in declared) return emptyList<ProviderRequestRoute>()\n        val runtimeMediaType = if (logicalFixtureMediaType == "anime") "tv" else logicalFixtureMediaType\n        return listOf<ProviderRequestRoute>(ProviderRequestRoute(runtimeMediaType))\n    }}\n'''
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

    # QuickJS/JNI is not safe under parallel provider execution in the native
    # clients. The full Labs proved this with macOS SIGBUS and Windows access
    # violations inside QuickJS while several providers were in flight. Keep the
    # generated coroutine shape, but serialize providers so every JS runtime has
    # exclusive process-local execution and still retains its own hard timeout.
    loop = "        for (providerBatch in providers.chunked(6)) {\n            val providerJobs = providerBatch.map { provider ->\n                async(Dispatchers.IO) {\n                    val started = System.currentTimeMillis()"
    replacement = f'''        for (providerBatch in providers.chunked(1)) {{\n            val providerJobs = providerBatch.map {{ provider ->\n                async(Dispatchers.IO) {{\n                    val logoProbe = probeLogo(provider.logo, providers.size == 1)\n                    emit("FIELD_NATIVE_ADDON_LOGO client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} configured=${{provider.logo.isNotBlank()}} state=${{logoProbe.state}} status=${{logoProbe.status}} content_type64=${{b64(logoProbe.contentType)}} host64=${{b64(logoProbe.host)}}")\n                    val requestRoutes = requestRoutesFor(provider.id, mediaType)\n                    if (requestRoutes.isEmpty()) {{\n                        emit("FIELD_NATIVE_PROVIDER_SKIPPED client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} enabled=${{provider.enabled}} requested_type=$logicalFixtureMediaType runtime_type=$mediaType declared_types64=${{b64(declaredTypesByProvider[provider.id.lowercase()].orEmpty().sorted().joinToString(","))}} reason=unsupported_type")\n                        return@async\n                    }}\n                    for (requestRoute in requestRoutes) {{\n                        val requestMediaType = requestRoute.mediaType\n                        val routeMode = "declared"\n                        val started = System.currentTimeMillis()\n                        emit("FIELD_NATIVE_PROVIDER_BEGIN client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} enabled=${{provider.enabled}} logical_type=$logicalFixtureMediaType request_type=$requestMediaType route_mode=$routeMode declared_types64=${{b64(declaredTypesByProvider[provider.id.lowercase()].orEmpty().sorted().joinToString(","))}}")'''
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

    # Adaptive catalogue rotations exist to resample clean zero-stream provider
    # routes. Production-player smoke is already collected on the primary corpus.
    # Do not let one hostile/buggy media URL abort an otherwise valid adaptive
    # provider traversal (the TV evidence showed exactly this on The 100/StreamZo).
    disable_player = os.environ.get("NIAKVIO_NATIVE_DISABLE_PLAYER_PROBES", "").strip() == "1"
    if disable_player and client in {"tv", "mobile"}:
        text, disabled_count = re.subn(
            r"rows\.take\(\d+\)\.forEachIndexed",
            "rows.take(0).forEachIndexed",
            text,
            count=1,
        )
        if disabled_count != 1:
            raise SystemExit(f"adaptive player-disable anchor count={disabled_count} client={client}")

    end_anchor = '                }\n            }\n            providerJobs.awaitAll()\n        }\n        emit("FIELD_NATIVE_CORPUS_END client=' + client
    text = replace_once(
        text,
        end_anchor,
        '                    }\n                }\n            }\n            providerJobs.awaitAll()\n        }\n        emit("FIELD_NATIVE_CORPUS_END client=' + client,
        "nested request loop close",
    )

    path.write_text(text, encoding="utf-8")
    print(
        f"FIELD_NATIVE_REQUEST_CONTRACT client={client} fixture={slug} media_type={resolved_fixture_media_type} "
        f"canonical_selection=true anime_runtime_alias=tv providers={len(types)} provider_batch_size=1 "
        f"player_probes_disabled={str(disable_player).lower()} path={path}"
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